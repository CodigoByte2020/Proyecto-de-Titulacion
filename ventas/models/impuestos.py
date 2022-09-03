from odoo import fields, models


class Impuesto(models.Model):
    _name = 'impuesto'

    name = fields.Char(string='Nombre del impuesto', required=True)
    amount = fields.Float(string='Importe', required=True)
