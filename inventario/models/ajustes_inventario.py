from odoo import api, fields, models


class AjustesInventario(models.Model):
    _name = 'ajustes.inventario'

    name = fields.Char(string='Nombre', required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    detalle_ajuste_inventario_ids = fields.One2many(
        'detalle.ajustes.inventario',
        'ajuste_inventario_id',
        string='Detalles'
    )


class DetalleAjustesInventario(models.Model):
    _name = 'detalle.ajustes.inventario'

    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    fecha = fields.Date(default=fields.Date.today(), string='Fecha')
    ajuste_inventario_id = fields.Many2one('ajustes.inventario', string='Ajuste inventario')
