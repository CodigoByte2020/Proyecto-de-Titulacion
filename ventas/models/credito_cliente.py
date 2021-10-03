from odoo import api, fields, models

STATE_DEUDA_SELECTION = [
    ('vigente', 'Vigente'),
    ('pagado', 'Pagado')
]


class CreditoCliente(models.Model):
    _name = 'ventas.credito.cliente'
    _description = 'Crédito de clientes'

    name = fields.Char(string='Número', default='/', copy=False)
    cliente_id = fields.Many2one('ventas.cliente', string='Cliente', required=True)
    limite_credito = fields.Float(string='Límite de crédito')
    deuda = fields.Float(string='Deuda')
    estado = fields.Selection(STATE_DEUDA_SELECTION, string='Estado')
    comentario = fields.Text(string='Comentario')
    pago_credito_clientes_ids = fields.One2many(
        'ventas.pago.credito.cliente',
        'credito_cliente_id',
        string='Pagos de crédito'
    )

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
    _name = 'ventas.pago.credito.cliente'
    _description = 'Registro de pagos de crédito de clientes'

    name = fields.Char(string='Número', default='/', copy=False)
    credito_cliente_id = fields.Many2one('ventas.credito.cliente', string='Cliente', required=True)
    monto = fields.Float(string='Monto')
    fecha_pago = fields.Date(string='Fecha de pago')

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    self._name, sequence_date=None) or '/'
            return super(PagoCreditoCliente, self).create(vals)
