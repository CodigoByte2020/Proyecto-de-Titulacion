from odoo import api, fields, models

from odoo.addons.estructura_base.models.constantes import (
    BORRADOR,
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)


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

    # Dentro del método create se usa el método update, no se puede utilizar el método create o write
    @api.model
    def create(self, values):
        record = super(CreditoCliente, self).create(values)

        # Actualizamos el campo credito_cliente_id del cliente elegido, recordar que un cliente sólo puede tener un crédito
        record.cliente_id.update({'credito_cliente_id': record.id})

        # cliente = self.env['base.persona'].browse(record.cliente_id.id)
        # cliente.update({'credito_cliente_id': record.id})

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
    state = fields.Selection(STATE_SELECTION, default=BORRADOR, string='Estado')
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)],
                                 states={CONFIRMADO: [('readonly', True)]})
    credito_cliente_id = fields.Many2one(related='cliente_id.credito_cliente_id', string='Crédito', readonly=True)
    monto = fields.Float(string='Monto', states={CONFIRMADO: [('readonly', True)]})
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha', readonly=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    currency_id = fields.Many2one(related='credito_cliente_id.currency_id')
    deuda_actual = fields.Float(string='Deuda actual', readonly=True)

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'
        values['state'] = PENDIENTE
        return super(PagoCreditoCliente, self).create(values)

    def action_set_confirm(self):
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        domain = [('credito_cliente_id', '=', self.credito_cliente_id.id)]
        ultimo_movimiento = self.env['movimientos.credito.cliente'].search(domain, order='fecha DESC', limit=1)
        movimiento = {
            'tipo': 'payment',
            'user_id': self.user_id.id,
            'fecha': self.fecha,
            'monto': self.monto,
            'deuda': ultimo_movimiento.deuda - self.monto,
            'credito_cliente_id': self.credito_cliente_id.id,
            'cliente_id': self.credito_cliente_id.cliente_id.id
        }
        self.env['movimientos.credito.cliente'].create(movimiento)

    # @api.onchange('credito_cliente_id')
    # def _onchange_deuda_actual(self):
    #     if self.credito_cliente_id:
    #         deuda = self.env['movimientos.credito.cliente'].search([
    #             ('credito_cliente_id', '=', self.credito_cliente_id.id)], order='fecha DESC', limit=1).deuda
    #         return {'value': {'deuda_actual': deuda}}
    #     else:
    #         return {'value': {'deuda_actual': False}}

    # TODO: El método se invoca en un pseudo-registro que contiene los valores presentes en el formulario, revisar documentación, PELIGRO ***
    # @api.onchange('cliente_id')
    # def _onchange_credito_cliente_id(self):
    #     if self.cliente_id:
    #         credito_cliente_id = self.env['credito.cliente'].search([('cliente_id', '=', self.cliente_id.id)]).id
    #         # self.update({'credito_cliente_id': credito_cliente_id})
    #         self.credito_cliente_id = credito_cliente_id
    #     else:
    #         # self.update({'credito_cliente_id': False})
    #         self.credito_cliente_id = False

    # @api.constrains('monto')
    # def _check_monto(self):
    #     for rec in self:
    #         if rec.monto > rec.deuda_actual:
    #             raise ValueError(f'El cliente {rec.cliente_id.name} no tiene ningun crédito registrado.')
