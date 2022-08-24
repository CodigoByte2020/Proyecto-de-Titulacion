from odoo import api, fields, models


class CreditoCliente(models.Model):
    _name = 'credito.cliente'
    _description = 'Crédito de clientes'
    _rec_name = 'cliente_id'

    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one(
        'res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True, store=True
    )
    comentario = fields.Text(string='Comentario')
    deuda_inicial = fields.Float(string='Deuda inicial')
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    pago_credito_clientes_ids = fields.One2many(
        'pago.credito.cliente',
        'credito_cliente_id',
        string='Pagos de crédito'
    )
    credito_alerta_id = fields.Many2one('credito.alerta', string='Alerta', required=True,
                                        help='Monto para alertar la deuda total del cliente.')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    _sql_constraints = [
        ('cliente_id', 'UNIQUE(cliente_id)', 'El cliente ya tiene un crédito registrado. !!!')
    ]

    @api.model
    def create(self, values):
        record = super(CreditoCliente, self).create(values)
        movimiento = {
            'credito_cliente_id': record.id,
            'tipo': 'customer_credit',
            'fecha': record.fecha,
            'monto': record.deuda_inicial,
            'deuda': record.deuda_inicial,
            'user_id': record.user_id.id,
            'cliente_id': record.cliente_id.id
        }
        self.env['movimientos.credito.cliente'].create(movimiento)
        return record

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f'{self.cliente_id.name} - {self.credito_alerta_id.display_name}'))
        return result


class PagoCreditoCliente(models.Model):
    _name = 'pago.credito.cliente'
    _description = 'Pago de crédito de clientes'

    name = fields.Char(string='Número', default='/', copy=False)
    credito_cliente_id = fields.Many2one('credito.cliente', string='Cliente', required=True)
    monto = fields.Float(string='Monto')
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    currency_id = fields.Many2one(related='credito_cliente_id.currency_id')

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'

        rec = super(PagoCreditoCliente, self).create(values)
        domain = [('credito_cliente_id', '=', rec.credito_cliente_id.id)]
        ultimo_movimiento = self.env['movimientos.credito.cliente'].search(domain, order='fecha DESC', limit=1)
        movimiento = {
            'tipo': 'payment',
            'user_id': rec.user_id.id,
            'fecha': rec.fecha,
            'monto': rec.monto,
            'deuda': ultimo_movimiento.deuda - rec.monto,
            'credito_cliente_id': rec.credito_cliente_id.id,
            'cliente_id': rec.credito_cliente_id.cliente_id.id
        }
        self.env['movimientos.credito.cliente'].create(movimiento)
        return rec
