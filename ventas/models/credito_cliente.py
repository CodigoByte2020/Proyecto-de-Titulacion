from odoo import api, fields, models


class CreditoCliente(models.Model):
    _name = 'credito.cliente'
    _description = 'Crédito de clientes'

    name = fields.Char(string='Número', default='/', copy=False)
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    limite_credito = fields.Float(string='Límite de crédito')
    comentario = fields.Text(string='Comentario')
    pago_credito_clientes_ids = fields.One2many(
        'pago.credito.cliente',
        'credito_cliente_id',
        string='Pagos de crédito'
    )

    # Campos calculados:
    # deuda = fields.Float(string='Deuda')
    # saldo = fields.Float(string='Saldo')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    self._name, sequence_date=None) or '/'
            return super(CreditoCliente, self).create(vals)


class PagoCreditoCliente(models.Model):
    _name = 'pago.credito.cliente'
    _description = 'Pago de crédito de clientes'

    credito_cliente_id = fields.Many2one('credito.cliente', string='Cliente', required=True)
    monto = fields.Float(string='Monto')
    fecha_pago = fields.Date(default=fields.Date.today(), string='Fecha de pago')
