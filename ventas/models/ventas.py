from odoo import api, fields, models

from odoo.addons.estructura_base.models.constantes import (
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    state = fields.Selection(STATE_SELECTION, default=PENDIENTE, string='Estado')
    cliente_id = fields.Many2one(
        'base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)],
        states={CONFIRMADO: [('readonly', True)]}
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(
        TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta',
        states={CONFIRMADO: [('readonly', True)]}
    )
    fecha = fields.Date(default=fields.Date.today(), string='Fecha', readonly=True)
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        string='Líneas de pedido'
    )

    def action_set_confirm(self):
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        detalle_ventas = self.env['detalle.ventas'].search([('venta_id', '=', self.id)])
        if detalle_ventas:
            for rec in detalle_ventas:
                movimiento = {
                    'tipo': 'out',
                    'user_id': self.user_id.id,
                    'fecha': self.fecha,
                    'producto_id': rec.producto_id.id,
                    'cantidad': rec.cantidad
                }
                self.env['movimientos'].create(movimiento)

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(
                    self._name, sequence_date=None) or '/'
        return super(Ventas, self).create(values)

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
    precio = fields.Float(related='producto_id.precio', string='Precio')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('cantidad', 'precio')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio:
                rec.write({'subtotal': rec.cantidad * rec.precio})

    def crear_movimientos(self, rec):
        venta = self.env['ventas'].search([('id', '=', rec.venta_id.id), ('state', '=', CONFIRMADO)])
        if venta:
            movimiento = {
                'tipo': 'out',
                'user_id': venta.user_id.id,
                'fecha': venta.fecha,
                'producto_id': rec.producto_id.id,
                'cantidad': rec.cantidad
            }
            self.env['movimientos'].create(movimiento)

    @api.model
    def create(self, values):
         rec = super(DetalleVentas, self).create(values)
         self.crear_movimientos(rec)
         return rec
