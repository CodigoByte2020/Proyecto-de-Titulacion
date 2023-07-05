# ORDEN DE LOS MÉTODOS Y SU EJECUCIÓN:
# 1. MÉTODO CREATE DEL REGISTRO PADRE
# 2. MÉTODO CREATE DEL REGISTRO HIJO
# 3. MÉTODO QUE ESTA SIENDO LLAMADO

import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.estructura_base.models.constantes import (
    CONFIRMADO,
    UTILIZADO
)

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]

TYPE_DOCUMENT_SELECTION = [
    ('invoice', 'Factura'),
    ('ticket', 'Boleta')
]


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    # def _domain_credit_note_id(self):
    #     credit_notes = self.env['credit.note'].search([('cliente_id', '=', self.cliente_id.id)])
    #     return [('id', 'in', credit_notes.ids)]

    name = fields.Char(string='Número', default='/', copy=False)
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta')
    fecha = fields.Date(default=fields.Date.today(), readonly=True, string='Fecha')
    amount_untaxed = fields.Float(compute='_compute_total', store=True, string='Ope. Gravadas')
    amount_tax = fields.Float(compute='_compute_total', store=True, string='IGV 18%')
    total = fields.Float(compute='_compute_total', store=True, string='Importe Total')
    comentarios = fields.Text(string='Comentarios')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        string='Líneas de pedido'
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, string='Moneda')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Compañía')
    type_document = fields.Selection(TYPE_DOCUMENT_SELECTION, default='invoice', string='Tipo de documento')
    # apply_credit_note = fields.Boolean(default=False, string='¿Aplica Nota de Crédito?')
    credit_note_id = fields.Many2one('credit.note', string='Nota de Crédito')
    total_credit_note = fields.Float(related='credit_note_id.total', store=True, string='Descuento')

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

    def _set_credit_note_state(self, values):
        credit_note_id = self.env['credit.note'].browse(values.get('credit_note_id'))
        if credit_note_id:
            credit_note_id.update({'state': UTILIZADO})

    # FIXME: REVISAR ESTOS MÉTODOS AL CREAR UNA VENTA (CREATE Y WRITE)
    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'
        self._set_credit_note_state(values)
        return super(Ventas, self).create(values)

    def write(self, values):
        self._set_credit_note_state(values)
        if self.credit_note_id:
            self.credit_note_id.update({'state': CONFIRMADO})
        return super(Ventas, self).write(values)

    @api.constrains('tipo_venta')
    def _check_tipo_venta(self):
        for rec in self:
            if rec.tipo_venta == 'credito':
                credito = self.env['credito.cliente'].search([('cliente_id', '=', rec.cliente_id.id)])
                if not credito:
                    raise ValidationError(f'El cliente {rec.cliente_id.name} no tiene ningun crédito registrado.')

    @api.constrains('total_credit_note')
    def _check_total_credit_note(self):
        for move in self:
            total = sum(move.detalle_ventas_ids.mapped('subtotal'))
            if total <= move.total_credit_note:
                raise ValidationError(f'El monto de la Nota de Crédito es {move.total_credit_note} y este debe ser '
                                      f'menor o igual al total de la factura -> {total}.')

    # FIXME: REVISAR PORQUE AL CREAR UNA VENTA CON UNA NOTA DE CRÉDITO, ACTUALIZAMOS EL NAVEGADOR Y LUEGO EDITAMOS, EL FILTRO NO FUNCIONA
    @api.onchange('cliente_id')
    def _onchange_cliente_id(self):
        self.update({'credit_note_id': False})
        if self.cliente_id:
            return {
                'domain': {'credit_note_id': [('cliente_id', '=', self.cliente_id.id), ('state', '=', 'confirmed')]}
            }
        return {'domain': {'credit_note_id': [('id', '=', -1)]}}

    # @api.onchange('apply_credit_note')
    # def _onchange_apply_credit_note(self):
    #     if not self.apply_credit_note:
    #         self.update({'credit_note_id': False})

    @api.depends('detalle_ventas_ids.subtotal')
    def _compute_total(self):
        for move in self:
            total = sum(move.detalle_ventas_ids.mapped('subtotal'))
            amount_tax = total * 0.18
            move.update({
                'amount_untaxed': total - amount_tax,
                'amount_tax': amount_tax,
                'total': total - self.total_credit_note
            })


class DetalleVentas(models.Model):
    _name = 'detalle.ventas'
    _description = 'Líneas de pedido de ventas'

    venta_id = fields.Many2one('ventas', string='Venta', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio_venta = fields.Float(compute='_compute_precio_venta', string='Precio unitario')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='venta_id.currency_id')

    # FIXME:
    #  INVESTIGAR UNA POSIBLE SOLUCIÓN PARA QUE LOS CAMPOS DE TOTALES DE VENTA SE MODIFIQUEN DESDE LA INTERFAZ AL
    #  CAMBIAR UN LINEA DE DETALLE
    # def _get_price_subtotal(self, cantidad=None, precio_venta=None):
    #     self.ensure_one()
    #     return self._get_price_subtotal_model(cantidad=cantidad or self.cantidad, precio_venta=precio_venta or self.precio_venta)
    #
    # @api.model
    # def _get_price_subtotal_model(self, cantidad, precio_venta):
    #     subtotal = cantidad * precio_venta
    #     res = {'subtotal': subtotal}
    #     return res
    #
    # @api.onchange('cantidad', 'precio_venta')
    # def _onchange_subtotal(self):
    #     for line in self:
    #         line.update(line._get_price_subtotal())

    @api.depends('producto_id')
    def _compute_precio_venta(self):
        for rec in self:
            sales_price_history_ids = rec.producto_id.sales_price_history_ids.filtered(
                lambda x: x.modified_date <= rec.venta_id.fecha)
            new_price = sales_price_history_ids and sales_price_history_ids.sorted(
                key=lambda x: x.modified_date)[-1].new_price
            rec.update({'precio_venta': new_price})

    @api.depends('cantidad', 'precio_venta')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio_venta:
                rec.update({'subtotal': rec.cantidad * rec.precio_venta})

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
        last_movement = movements_model.search([('producto_id', '=', self.producto_id.id)], order='create_date DESC',
                                               limit=1)
        movements_model.create({
            'detalle_venta_id': [(4, self.id, False)],
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

    detalle_venta_id = fields.Many2many('detalle.ventas')
