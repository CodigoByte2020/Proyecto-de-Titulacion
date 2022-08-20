from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.estructura_base.models.constantes import (
    BORRADOR,
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]

# Orden de los metodos y su ejecución:
# 1. Método create del padre
# 2. Método create del hijo
# 3. Método en cuestión que ha sido llamado


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    state = fields.Selection(STATE_SELECTION, default=BORRADOR, string='Estado')
    cliente_id = fields.Many2one(
        'base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)],
        states={CONFIRMADO: [('readonly', True)]}
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(
        TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta',
        states={CONFIRMADO: [('readonly', True)]}
    )
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha',
                            states={CONFIRMADO: [('readonly', True)]})
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        states={CONFIRMADO: [('readonly', True)]},
        string='Líneas de pedido'
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    '''
    Busca el último movimiento registrado que pertenezca al producto en cuestión, para calcular el total.
    Crea un registro de movimiento de inventario, por cada línea de venta.
    Crea un registro de movimiento de crédito de cliente por venta.'''
    def action_set_confirm(self):
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        detalle_ventas = self.env['detalle.ventas'].search([('venta_id', '=', self.id)])
        for rec in detalle_ventas:
            movements_model = self.env['movimientos']
            last_movement = movements_model.search([('producto_id', '=', rec.producto_id.id)],
                                                   order='create_date DESC', limit=1)
            if not last_movement:
                raise ValidationError('No se ha registrado ningúna compra o ajuste de inventario correspondiente al '
                                      'producto {}'.format(rec.producto_id.name))
            movements_model.create({
                'tipo': 'out',
                'user_id': self.user_id.id,
                'fecha': self.fecha,
                'producto_id': rec.producto_id.id,
                'cantidad': rec.cantidad,
                'total': last_movement.total - rec.cantidad
            })

        credit_movement_model = self.env['movimientos.credito.cliente']
        domain = [('cliente_id', '=', self.cliente_id.id)]
        last_credit_movement = credit_movement_model.search(domain, order='fecha DESC', limit=1)
        deuda_total = last_credit_movement.deuda + self.total
        monto = last_credit_movement.credito_cliente_id.credito_alerta_id.monto

        if self.tipo_venta == 'credito' and deuda_total > monto:
            raise ValidationError(f'El cliente {self.cliente_id.name} tiene un límite de crédito de '
                                  f'{self.currency_id.symbol} {monto} y este ha sido superado')

        if self.tipo_venta == 'credito':
            credit_movement_model.create({
                'cliente_id': self.cliente_id.id,
                'tipo': 'sale',
                'user_id': self.user_id.id,
                'fecha': self.fecha,
                'monto': self.total,
                'deuda': deuda_total,
                'credito_cliente_id': last_credit_movement.credito_cliente_id.id
            })

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'
        values['state'] = PENDIENTE
        return super(Ventas, self).create(values)

    @api.constrains('tipo_venta')
    def _check_tipo_venta(self):
        for rec in self:
            if rec.tipo_venta == 'credito':
                credito = self.env['credito.cliente'].search([('cliente_id', '=', rec.cliente_id.id)])
                if not credito:
                    raise ValidationError(f'El cliente {rec.cliente_id.name} no tiene ningun crédito registrado.')

    # Programación Imperativa: Se describe paso a paso.
    # for rec in self:
    #     total = 0
    #     records = self.env['ventas.detalle.ventas'].search([('venta_id', '=', rec.id)])
    #     for i in records:
    #         total = total + i.subtotal
    #     rec.write({'total': total})

    # Programación Declarativa: Se describe el resultado final.
    # Self es el registro de venta actual
    @api.depends('detalle_ventas_ids')
    def _compute_total(self):
        for rec in self:
            total = sum(rec.detalle_ventas_ids.mapped('subtotal'))
            rec.write({'total': total})


class DetalleVentas(models.Model):
    _name = 'detalle.ventas'
    _description = 'Líneas de pedido de ventas'

    venta_id = fields.Many2one('ventas', string='Venta', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio_venta = fields.Float(related='producto_id.precio_venta', string='Precio')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='venta_id.currency_id')

    @api.depends('cantidad', 'precio_venta')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio_venta:
                rec.write({'subtotal': rec.cantidad * rec.precio_venta})
