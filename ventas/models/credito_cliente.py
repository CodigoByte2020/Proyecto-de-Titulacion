from odoo import api, fields, models


class CreditoCliente(models.Model):
    _name = 'credito.cliente'
    _description = 'Crédito de clientes'

    name = fields.Char(string='Nombre')
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True, store=True
    )
    comentario = fields.Text(string='Comentario')
    deuda = fields.Float(string='Deuda', required=True)
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    pago_credito_clientes_ids = fields.One2many(
        'pago.credito.cliente',
        'credito_cliente_id',
        string='Pagos de crédito'
    )

    # Falta validar que sólo se pueda crear un crédito por cliente
    # OK
    @api.model
    def create(self, values):
        print('jajjsajsaj')
        record = super(CreditoCliente, self).create(values)
        movimiento = {
            'name': record.name,
            'credito_cliente_id': record.id,
            'tipo': 'customer_credit',
            'fecha': record.fecha,
            'monto': record.deuda,
            'deuda': record.deuda,
            'user_id': record.user_id.id
        }
        self.env['movimientos.credito.cliente'].create(movimiento)
        return record


class PagoCreditoCliente(models.Model):
    _name = 'pago.credito.cliente'
    _description = 'Pago de crédito de clientes'

    credito_cliente_id = fields.Many2one('credito.cliente', string='Cliente', required=True)
    monto = fields.Float(string='Monto')
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)

    @api.model
    def create(self, values):
        rec = super(PagoCreditoCliente, self).create(values)
        domain = [('credito_cliente_id', '=', rec.credito_cliente_id.id)]
        ultimo_movimiento = self.env['movimientos.credito.cliente'].search(domain, order='fecha DESC', limit=1)
        movimiento = {
            'tipo': 'payment',
            'user_id': rec.user_id.id,
            'fecha': rec.fecha,
            'monto': rec.monto,
            'deuda': ultimo_movimiento.deuda - rec.monto,
            'credito_cliente_id': rec.credito_cliente_id.id
        }
        self.env['movimientos.credito.cliente'].create(movimiento)
        return rec
