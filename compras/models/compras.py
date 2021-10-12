from odoo import api, fields, models

from odoo.addons.estructura_base.models.constantes import (
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)


class Compras(models.Model):
    _name = 'compras'
    _description = 'Registro de compras'

    name = fields.Char(string='Número', default='/', copy=False)
    state = fields.Selection(STATE_SELECTION, default=PENDIENTE, string='Estado')
    proveedor_id = fields.Many2one(
        'base.persona', string='Proveedor', required=True, domain=[('rango_proveedor', '=', 1)],
        states={CONFIRMADO: [('readonly', True)]}
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_compras_ids = fields.One2many(
        'detalle.compras',
        'compra_id',
        string='Líneas de compra'
    )

    def action_set_confirm(self):
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        detalle_compras = self.env['detalle.compras'].search([('compra_id', '=', self.id)])
        if detalle_compras:
            for rec in detalle_compras:
                domain = [('producto_id', '=', rec.producto_id.id), ('tipo', 'in', ['in', 'aj'])]
                movimiento_anterior = self.env['movimientos'].search(domain, order='create_date DESC', limit=1)
                movimiento = {
                    'tipo': 'in',
                    'user_id': self.user_id.id,
                    'fecha': self.fecha,
                    'producto_id': rec.producto_id.id,
                    'cantidad': rec.cantidad,
                    'total': rec.cantidad + movimiento_anterior.total if movimiento_anterior else rec.cantidad
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
        return super(Compras, self).create(values)

    @api.depends('detalle_compras_ids')
    def _compute_total(self):
        for rec in self:
            total = sum(rec.detalle_compras_ids.mapped('subtotal'))
            rec.write({'total': total})


class DetalleCompras(models.Model):
    _name = 'detalle.compras'
    _description = 'Líneas de pedido de compras'

    compra_id = fields.Many2one('compras', string='Compra', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    subtotal = fields.Float(string='Subtotal')

    def crear_movimientos(self, rec):
        compra = self.env['compras'].search([('id', '=', rec.compra_id.id), ('state', '=', CONFIRMADO)])
        if compra:
            domain = [('producto_id', '=', rec.producto_id.id), ('tipo', 'in', ['in', 'aj'])]
            movimiento_anterior = self.env['movimientos'].search(domain, order='create_date DESC', limit=1)
            movimiento = {
                'tipo': 'in',
                'user_id': compra.user_id.id,
                'fecha': compra.fecha,
                'producto_id': rec.producto_id.id,
                'cantidad': rec.cantidad,
                'total': rec.cantidad + movimiento_anterior.total if movimiento_anterior else rec.cantidad
            }
            self.env['movimientos'].create(movimiento)

    @api.model
    def create(self, values):
         rec = super(DetalleCompras, self).create(values)
         self.crear_movimientos(rec)
         return rec
        