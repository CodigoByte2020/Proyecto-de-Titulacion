from odoo import api, fields, models

TIPO_MOVIMIENTO_SELECTION = [
    ('in', 'Entrada'),
    ('out', 'Salida'),
    ('aj', 'Ajuste')
]


class Movimientos(models.Model):
    _name = 'movimientos'
    _description = 'Movimientos de inventario.'

    tipo = fields.Selection(TIPO_MOVIMIENTO_SELECTION, string='Tipo')
    user_id = fields.Many2one('res.users', string='Responsable', readonly=True)
    fecha = fields.Datetime(string='Fecha')
    producto_id = fields.Many2one('base.producto')
    cantidad = fields.Float(string='Cantidad', group_operator=False)
    total = fields.Float(string='Total', group_operator=False)
