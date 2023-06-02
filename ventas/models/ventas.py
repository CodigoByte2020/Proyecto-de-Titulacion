# ORDEN DE LOS MÉTODOS Y SU EJECUCIÓN:
# 1. MÉTODO CREATE DEL REGISTRO PADRE
# 2. MÉTODO CREATE DEL REGISTRO HIJO
# 3. MÉTODO QUE ESTA SIENDO LLAMADO

import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta')
    fecha = fields.Date(default=fields.Date.today(), string='Fecha', readonly=True)
    amount_untaxed = fields.Float(compute='_compute_total', store=True, string='Ope. Gravadas')
    amount_tax = fields.Float(compute='_compute_total', store=True, string='IGV 18%')
    total = fields.Float(compute='_compute_total', store=True, string='Importe Total')
    comentarios = fields.Text(string='Comentarios')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        string='Líneas de pedido'
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Compañía')

    # Crea un registro de movimiento de crédito de cliente por venta.
    # def action_set_confirm(self):
    #     credit_movement_model = self.env['movimientos.credito.cliente']
    #     domain = [('cliente_id', '=', self.cliente_id.id)]
    #     last_credit_movement = credit_movement_model.search(domain, order='fecha DESC', limit=1)
    #     deuda_total = last_credit_movement.deuda + self.total
    #     monto = last_credit_movement.credito_cliente_id.credito_alerta_id.monto
    #     if self.tipo_venta == 'credito' and deuda_total > monto:
    #         raise ValidationError(f'El cliente {self.cliente_id.name} tiene un límite de crédito de '
    #                               f'{self.currency_id.symbol} {monto} y este ha sido superado')
    #     if self.tipo_venta == 'credito':
    #         credit_movement_model.create({
    #             'cliente_id': self.cliente_id.id,
    #             'tipo': 'sale',
    #             'user_id': self.user_id.id,
    #             'fecha': datetime.datetime.now(),
    #             'monto': self.total,
    #             'deuda': deuda_total,
    #             'credito_cliente_id': last_credit_movement.credito_cliente_id.id
    #         })

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'
        return super(Ventas, self).create(values)

    @api.constrains('tipo_venta')
    def _check_tipo_venta(self):
        for rec in self:
            if rec.tipo_venta == 'credito':
                credito = self.env['credito.cliente'].search([('cliente_id', '=', rec.cliente_id.id)])
                if not credito:
                    raise ValidationError(f'El cliente {rec.cliente_id.name} no tiene ningun crédito registrado.')

    @api.depends('detalle_ventas_ids.subtotal')
    def _compute_total(self):
        for move in self:
            total = sum(move.detalle_ventas_ids.mapped('subtotal'))
            amount_tax = total * 0.18
            # move.update({
            #     'amount_untaxed': total - amount_tax,
            #     'amount_tax': amount_tax,
            #     'total': total
            # })
            move.total = total


class DetalleVentas(models.Model):
    _name = 'detalle.ventas'
    _description = 'Líneas de pedido de ventas'

    venta_id = fields.Many2one('ventas', string='Venta', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio_venta = fields.Float(related='producto_id.precio_venta', string='Precio unitario')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='venta_id.currency_id')


    # FIXME:
    #  INVESTIGAR UNA POSIBLE SOLUCIÓN PARA QUE LOS CAMPOS DE TOTALES DE VENTA SE MODIFIQUEN DESDE LA INTERFAZ AL
    #  CAMBIAR UN LINEA DE DETALLE
    def _get_price_subtotal(self, cantidad=None, precio_venta=None):
        self.ensure_one()
        return self._get_price_subtotal_model(cantidad=cantidad or self.cantidad, precio_venta=precio_venta or self.precio_venta)

    @api.model
    def _get_price_subtotal_model(self, cantidad, precio_venta):
        subtotal = cantidad * precio_venta
        res = {'subtotal': subtotal}
        return res

    @api.onchange('cantidad', 'precio_venta')
    def _onchange_subtotal(self):
        for line in self:
            line.update(line._get_price_subtotal())

    # @api.depends('cantidad', 'precio_venta')
    # def _compute_subtotal(self):
    #     for rec in self:
    #         if rec.cantidad and rec.precio_venta:
    #             rec.update({'subtotal': rec.cantidad * rec.precio_venta})

    def validate_stock(self):
        quantity_product = self.env['movimientos'].search([('producto_id', '=', self.producto_id.id)],
                                                          order='create_date DESC', limit=1).total
        if self.cantidad > quantity_product:
            raise ValidationError(f'No existe suficiente stock de inventario para el Producto {self.producto_id.name}\n'
                                  f'Asegúrese de tener el inventario actualizado para registrar la venta correctamente')

    def update_validate_stock(self):
        movements_model = self.env['movimientos']
        movement = movements_model.search([('detalle_venta_id', '=', self.id)])
        quantity_product = (movements_model.search([('producto_id', '=', self.producto_id.id)],
                                                   order='create_date DESC', limit=2) - movement).total
        if self.cantidad > quantity_product:
            raise ValidationError(f'No existe suficiente stock de inventario para el Producto {self.producto_id.name}\n'
                                  f'Asegúrese de tener el inventario actualizado para registrar la venta correctamente')

    def create_movement(self):
        movements_model = self.env['movimientos']
        last_movement = movements_model.search([('producto_id', '=', self.producto_id.id)],
                                               order='create_date DESC', limit=1)
        movements_model.create({
            'detalle_venta_id': self.id,
            'tipo': 'out',
            'user_id': self.venta_id.user_id.id,
            'fecha': datetime.datetime.now(),
            'producto_id': self.producto_id.id,
            'cantidad': self.cantidad,
            'total': last_movement.total - self.cantidad,
        })

    def update_movement(self):
        movements_model = self.env['movimientos']
        movement = movements_model.search([('detalle_venta_id', '=', self.id)])
        last_movement = movements_model.search([('producto_id', '=', self.producto_id.id)],
                                               order='create_date DESC', limit=2) - movement
        movement.update({
            'fecha': datetime.datetime.now(),
            'producto_id': self.producto_id,
            'cantidad': self.cantidad,
            'total': last_movement.total - self.cantidad
        })

    @api.model
    def create(self, values):
        rec = super(DetalleVentas, self).create(values)
        rec.validate_stock()
        rec.create_movement()
        return rec

    def write(self, values):
        rec = super(DetalleVentas, self).write(values)
        self.update_validate_stock()
        self.update_movement()
        return rec


class Movimientos(models.Model):
    _inherit = 'movimientos'

    detalle_venta_id = fields.Many2one('detalle.ventas')
