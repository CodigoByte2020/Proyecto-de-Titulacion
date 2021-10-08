from odoo import api, fields, models

TIPO_MOVIMIENTO_SELECTION = [
    ('in', 'Entrada'),
    ('out', 'Salida'),
    ('aj', 'Ajuste')
]


class Movimientos(models.Model):
    _name = 'movimientos'

    tipo = fields.Selection(TIPO_MOVIMIENTO_SELECTION, string='Tipo')
    user_id = fields.Many2one(string='Responsable', readonly=True)
    producto_id = fields.Many2one('base.producto')
    fecha = fields.Datetime(string='Fecha')
    cantidad = fields.Float(string='Cantidad')
    total = fields.Float(string='Total')
