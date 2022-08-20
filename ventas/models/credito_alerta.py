from odoo import api, fields, models


class CreditoAlerta(models.Model):
    _name = 'credito.alerta'
    _description = 'Alerta de créditos'

    monto = fields.Float(string='Monto', required=True)
    active = fields.Boolean(string='Activo', default=True)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f'{self.env.company.currency_id.symbol} {rec.monto}'))
        return result
