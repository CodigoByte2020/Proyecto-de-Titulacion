from odoo import api, fields, models


class CreditoCliente(models.Model):
    _name = 'credito.cliente'
    _description = 'Crédito de clientes'
    _rec_name = 'cliente_id'

    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    comentario = fields.Text(string='Comentario')
    deuda = fields.Float(string='Deuda')
    pago_credito_clientes_ids = fields.One2many(
        'pago.credito.cliente',
        'credito_cliente_id',
        string='Pagos de crédito'
    )

    # Campos calculados:
    # saldo = fields.Float(string='Saldo')


class PagoCreditoCliente(models.Model):
    _name = 'pago.credito.cliente'
    _description = 'Pago de crédito de clientes'

    credito_cliente_id = fields.Many2one('credito.cliente', string='Cliente', required=True)
    monto = fields.Float(string='Monto')
    fecha_pago = fields.Date(default=fields.Date.today(), string='Fecha de pago')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
