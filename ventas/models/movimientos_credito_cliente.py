from odoo import api, fields, models

TIPO_MOVIMIENTO_CREDITO_SELECTION = [
    ('customer_credit', 'Crédito de Cliente'),
    ('sale', 'Venta'),
    ('payment', 'Pago')
]


class MovimientosCreditoCliente(models.Model):
    _name = 'movimientos.credito.cliente'
    _rec_name = 'cliente_id'
    _order = 'fecha asc'

    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    tipo = fields.Selection(TIPO_MOVIMIENTO_CREDITO_SELECTION, string='Tipo')
    user_id = fields.Many2one('res.users', string='Responsable', readonly=True)
    fecha = fields.Datetime(string='Fecha')
    monto = fields.Float(string='Monto')
    deuda = fields.Float(string='Deuda')
    credito_cliente_id = fields.Many2one('credito.cliente', string='Crédito de Cliente')
