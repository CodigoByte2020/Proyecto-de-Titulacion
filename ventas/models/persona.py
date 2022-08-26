from odoo import api, fields, models


class Persona(models.Model):
    _inherit = 'base.persona'

    credito_cliente_id = fields.Many2one('credito.cliente', string='Límite de crédito')
    used_credit = fields.Monetary(string='Crédito utilizado', readonly=True)
    available_credit = fields.Monetary(string='Crédito disponible', readonly=True)

    def calculate_credit(self):
        deuda = self.env['movimientos.credito.cliente'].search([
            ('cliente_id', '=', self.id)], order='fecha DESC', limit=1).deuda
        self.write({
            'used_credit': deuda if self.credito_cliente_id else False,
            'available_credit': self.credito_cliente_id.credito_alerta_id.monto - deuda
            if self.credito_cliente_id else False
        })
