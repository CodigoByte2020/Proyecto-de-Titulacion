from odoo import api, fields, models

from odoo.addons.estructura_base.models.constantes import (
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)


class AjustesInventario(models.Model):
    _name = 'ajustes.inventario'

    name = fields.Char(string='Nombre', required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    state = fields.Selection(STATE_SELECTION, default=PENDIENTE, string='Estado')
    detalle_ajuste_inventario_ids = fields.One2many(
        'detalle.ajustes.inventario',
        'ajuste_inventario_id',
        string='Detalles'
    )

    def action_set_confirm(self):
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        detalle_inventario = self.env['detalle.ajustes.inventario'].search([('ajuste_inventario_id', '=', self.id)])
        if detalle_inventario:
            for rec in detalle_inventario:
                movimiento = {
                    'tipo': 'aj',
                    'user_id': self.user_id.id,
                    'fecha': rec.fecha,
                    'producto_id': rec.producto_id.id,
                    'cantidad': rec.cantidad,
                    'total': rec.cantidad
                }
                self.env['movimientos'].create(movimiento)


class DetalleAjustesInventario(models.Model):
    _name = 'detalle.ajustes.inventario'

    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    fecha = fields.Date(default=fields.Date.today(), string='Fecha')
    ajuste_inventario_id = fields.Many2one('ajustes.inventario', string='Ajuste inventario')

    def crear_movimientos(self, rec):
        domain = [('id', '=', rec.ajuste_inventario_id.id), ('state', '=', CONFIRMADO)]
        inventario = self.env['ajustes.inventario'].search(domain)
        if inventario:
            movimiento = {
                'tipo': 'out',
                'user_id': inventario.user_id.id,
                'fecha': inventario.fecha,
                'producto_id': rec.producto_id.id,
                'cantidad': rec.cantidad,
                'total': rec.cantidad
            }
            self.env['movimientos'].create(movimiento)

    @api.model
    def create(self, values):
         rec = super(DetalleAjustesInventario, self).create(values)
         self.crear_movimientos(rec)
         return rec
