import datetime

from odoo import api, fields, models
from odoo.exceptions import ValidationError

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

    state = fields.Selection(STATE_SELECTION, default=BORRADOR, string='Estado')
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)],
                                 states={CONFIRMADO: [('readonly', True)]})
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True,
                              store=True)
    comentario = fields.Text(string='Comentario')
    deuda_inicial = fields.Float(string='Deuda inicial', states={CONFIRMADO: [('readonly', True)]})
    fecha = fields.Datetime(default=fields.Date.today(), string='Fecha')
    pago_credito_clientes_ids = fields.One2many(
        'pago.credito.cliente',
        'credito_cliente_id',
        string='Pagos de crédito'
    )
    credito_alerta_id = fields.Many2one('credito.alerta', string='Límite de crédito', required=True,
                                        help='Monto para alertar la deuda total del cliente.')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    _sql_constraints = [
        ('cliente_id', 'UNIQUE(cliente_id)', 'Este cliente ya tiene un crédito registrado. !!!')
    ]

    # Dentro del método create se usa el método update, no se puede utilizar el método create o write
    @api.model
    def create(self, values):
        values['state'] = PENDIENTE
        return super(CreditoCliente, self).create(values)

    def action_set_confirm(self):
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        self.cliente_id.write({'credito_cliente_id': self.id})
        self.env['movimientos.credito.cliente'].create({
            'credito_cliente_id': self.id,
            'tipo': 'customer_credit',
            'fecha': datetime.datetime.now(),
            'monto': self.deuda_inicial,
            'deuda': self.deuda_inicial,
            'user_id': self.user_id.id,
            'cliente_id': self.cliente_id.id
        })

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f'{rec.cliente_id.name} - {rec.credito_alerta_id.display_name}'))
        return result

    @api.constrains('deuda_inicial')
    def _check_deuda_inicial(self):
        for rec in self:
            if rec.deuda_inicial > rec.credito_alerta_id.monto:
                raise ValidationError(f'La Deuda inicial debe ser menor o igual al Límite de crédito !!!')


class PagoCreditoCliente(models.Model):
    _name = 'pago.credito.cliente'
    _description = 'Pago de crédito de clientes'

    name = fields.Char(string='Número', default='/', copy=False)
    state = fields.Selection(STATE_SELECTION, default=BORRADOR, string='Estado')
    # cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)],
    #                              states={CONFIRMADO: [('readonly', True)]})
    credito_cliente_id = fields.Many2one('credito.cliente', string='Crédito', required=True)
    monto = fields.Float(string='Monto a pagar', states={CONFIRMADO: [('readonly', True)]}, required=True)
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha', readonly=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    currency_id = fields.Many2one(related='credito_cliente_id.currency_id')
    deuda_actual = fields.Float(string='Deuda actual', readonly=True, compute='_compute_deuda_actual', store=True)

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
            'fecha': datetime.datetime.now(),
            'monto': self.monto,
            'deuda': ultimo_movimiento.deuda - self.monto,
            'credito_cliente_id': self.credito_cliente_id.id,
            'cliente_id': self.credito_cliente_id.cliente_id.id
        }
        self.env['movimientos.credito.cliente'].create(movimiento)

    # Los métodos compute, funcionan a nivel de base de datos
    # Se puede asignar un valor por defecto a un campo que no sea relacional
    @api.depends('credito_cliente_id')
    def _compute_deuda_actual(self):
        for rec in self:
            if rec.credito_cliente_id:
                deuda = self.env['movimientos.credito.cliente'].search([
                    ('credito_cliente_id', '=', rec.credito_cliente_id.id)], order='fecha DESC', limit=1).deuda
                rec.write({'deuda_actual': deuda})
            else:
                rec.write({'deuda_actual': False})

    #El método se invoca en un pseudo-registro que contiene los valores presentes en el formulario, DOCUMENTACIÓN
    # @api.onchange('cliente_id')
    # def _onchange_cliente_id(self):
    #     self.update({'credito_cliente_id': False})
    #     if self.cliente_id:
    #         return {'domain': {'credito_cliente_id': [('cliente_id', '=', self.cliente_id.id)]}}
    #     else:
    #         return {'domain': {'credito_cliente_id': [('id', '=', -1)]}}

    @api.constrains('monto')
    def _check_monto(self):
        for rec in self:
            if rec.monto > rec.deuda_actual:
                raise ValidationError(f'El Monto a pagar debe ser menor o igual a la Deuda actual !!!')
