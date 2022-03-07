from odoo import api, fields, models


class CreditoAlerta(models.Model):
    _name = 'credito.alerta'
    _description = 'Alerta de créditos'
    _rec_name = 'monto'

    monto = fields.Char(string='Monto', required=True)
    active = fields.Boolean(string='Activo', default=True)
