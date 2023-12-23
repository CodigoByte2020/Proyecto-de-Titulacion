# ORDEN DE LOS MÉTODOS Y SU EJECUCIÓN:
# 1. MÉTODO CREATE DEL REGISTRO PADRE
# 2. MÉTODO CREATE DEL REGISTRO HIJO
# 3. MÉTODO QUE ESTA SIENDO LLAMADO

from datetime import datetime
from itertools import groupby

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.addons.estructura_base.models.constantes import (
    CONFIRMADO,
    PENDIENTE,
    UTILIZADO,
    CANCELADO,
    STATE_SELECTION
)

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]

TYPE_DOCUMENT_SELECTION = [
    ('invoice', 'Factura'),
    ('ticket', 'Boleta')
]


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta')
    fecha = fields.Date(default=fields.Date.today(), readonly=True, string='Fecha')
    amount_untaxed = fields.Float(compute='_compute_total', store=True, string='Ope. Gravadas')
    amount_tax = fields.Float(compute='_compute_total', store=True, string='IGV 18%')
    total = fields.Float(compute='_compute_total', store=True, string='Importe Total')
    comentarios = fields.Text(string='Comentarios')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        string='Líneas de pedido'
    )
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id, string='Moneda')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Compañía')
    type_document = fields.Selection(TYPE_DOCUMENT_SELECTION, default='invoice', string='Tipo de documento')
    state = fields.Selection(STATE_SELECTION, default=PENDIENTE, string='Estado')
    # credit_note_id = fields.Many2one('credit.note', string='Nota de Crédito',
    #                                  domain="[('cliente_id', '=', cliente_id), ('state', '=', 'confirmed')]")
                                     # domain=lambda self: [('cliente_id', '=', self._domain_credit_note_id()), ('state', '=', 'confirmed')])
                                     # domain=lambda self: [('cliente_id', '=', self.cliente_id.id), ('state', '=', 'confirmed')])
                                     # domain=_domain_credit_note_id)  REVISAR EN QUE OCASIONES ES MEJOR USAR ALGUNA DE ESTAS FORMAS
    # total_credit_note = fields.Float(related='credit_note_id.total', store=True, string='Descuento nota de crédito')
    # apply_credit_note = fields.Boolean(string='¿Aplicar nota de crédito?', default=False)

    # Crea un registro de movimiento de crédito de cliente por venta.
    # def action_set_confirm(self):
    #     credit_movement_model = self.env['movimientos.credito.cliente']
    #     domain = [('cliente_id', '=', self.cliente_id.id)]
    #     last_credit_movement = credit_movement_model.search(domain, order='fecha DESC', limit=1)
    #     deuda_total = last_credit_movement.deuda + self.total
    #     monto = last_credit_movement.credito_cliente_id.credito_alerta_id.monto
    #     if self.tipo_venta == 'credito' and deuda_total > monto:
    #         raise ValidationError(f'El cliente {self.cliente_id.name} tiene un límite de crédito de '
    #                               f'{self.currency_id.symbol} {monto} y este ha sido superado')
    #     if self.tipo_venta == 'credito':
    #         credit_movement_model.create({
    #             'cliente_id': self.cliente_id.id,
    #             'tipo': 'sale',
    #             'user_id': self.user_id.id,
    #             'fecha': datetime.datetime.now(),
    #             'monto': self.total,
    #             'deuda': deuda_total,
    #             'credito_cliente_id': last_credit_movement.credito_cliente_id.id
    #         })

    @api.constrains('tipo_venta')
    def _check_tipo_venta(self):
        for rec in self:
            if rec.tipo_venta == 'credito':
                credito = self.env['credito.cliente'].search([('cliente_id', '=', rec.cliente_id.id)])
                if not credito:
                    raise ValidationError(f'El cliente {rec.cliente_id.name} no tiene ningun crédito registrado.')

    # @api.constrains('total_credit_note')
    # def _check_total_credit_note(self):
    #     for move in self:
    #         total = sum(move.detalle_ventas_ids.mapped('subtotal'))
    #         if move.total_credit_note > total:
    #             raise ValidationError(f'El monto de la Nota de Crédito es {move.total_credit_note:,.2f} y este debe ser'
    #                                   f' menor o igual al total de la factura -> {total:,.2f}')

    # @api.constrains('credit_note_id')
    # def _check_credit_note_id(self):
    #     for move in self:
    #         if move.cliente_id.id != move.credit_note_id.cliente_id.id or move.credit_note_id.state != CONFIRMADO:
    #             raise ValidationError('La Nota de Crédito es incorrecta, por favor elija otra. !!!')

    # FIXME: - ERROR SOLUCIONADO CON:
    #  credit_note_id = fields.Many2one('credit.note', string='Nota de Crédito', domain="[('cliente_id', '=', cliente_id), ('state', '=', 'confirmed')]")
    #  REVISAR PORQUE AL CREAR UNA VENTA CON UNA NOTA DE CRÉDITO, ACTUALIZAMOS EL NAVEGADOR Y LUEGO EDITAMOS, EL FILTRO
    #  NO FUNCIONA. PREGUNTAR A JUAN DIEGO.
    #  PARA QUE FUNCIONE EL FILTRO SIN PROBLEMA, SIEMPRE SELECCIONAR EL CLIENTE, ASÍ ESTE VALOR YA ESTE ESTABLECIDO.
    # @api.onchange('cliente_id')
    # def _onchange_cliente_id(self):
    #     self.update({'credit_note_id': False})
    #     if self.cliente_id:
    #         return {'domain': {'credit_note_id': [('cliente_id', '=', self.cliente_id.id), ('state', '=', CONFIRMADO)]}}
    #     return {'domain': {'credit_note_id': [('id', '=', -1)]}}

    # @api.onchange('apply_credit_note')
    # def _onchange_apply_credit_note(self):
    #     if not self.apply_credit_note:
    #         self.update({'credit_note_id': False})
    #
    # @api.onchange('credit_note_id')
    # def _onchange_credit_note_id(self):
    #     if not self.credit_note_id:
    #         self.update({'total_credit_note': False})
    #
    # @api.onchange('cliente_id')
    # def _onchange_cliente_id(self):
    #     if self.credit_note_id:
    #         self.update({'credit_note_id': False})

    # @api.depends('detalle_ventas_ids.subtotal', 'credit_note_id')
    @api.depends('detalle_ventas_ids.subtotal')
    def _compute_total(self):
        for move in self:
            total = sum(move.detalle_ventas_ids.mapped('subtotal'))
            amount_tax = total * 0.18
            move.update({
                'amount_untaxed': total - amount_tax,
                'amount_tax': amount_tax,
                # 'total': total - self.total_credit_note
                'total': total
            })

    # def _set_credit_note_state(self, values):
    #     credit_note_id = self.env['credit.note'].browse(values.get('credit_note_id'))
    #     if credit_note_id:
    #         credit_note_id.update({'state': UTILIZADO})

    def action_set_confirm(self):
        self.detalle_ventas_ids.mapped(lambda record: record.action_set_confirm())
        self.write({'state': CONFIRMADO})

    def action_set_cancel(self):
        self.detalle_ventas_ids.mapped(lambda record: record.action_set_cancel())
        self.write({'state': CANCELADO})

    # FIXME: REVISAR ESTOS MÉTODOS AL CREAR UNA VENTA (CREATE Y WRITE)
    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(
                    force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'
        # self._set_credit_note_state(values)
        return super(Ventas, self).create(values)

    # def write(self, values):
    #     self._set_credit_note_state(values)
    #     if self.credit_note_id:
    #         self.credit_note_id.update({'state': CONFIRMADO})
    #     return super(Ventas, self).write(values)

    # @api.model
    # def model_function(self):
    #     print('@api.model')

    # def read(self, fields, load='_classic_read'):
    #     """ Without this call, dynamic fields build by fields_view_get()
    #         generate a log warning, i.e.:
    #         odoo.models:mass.editing.wizard.read() with unknown field 'myfield'
    #         odoo.models:mass.editing.wizard.read()
    #             with unknown field 'selection__myfield'
    #     """
    #     real_fields = fields
    #     if fields:
    #         # We remove fields which are not in _fields
    #         real_fields = [x for x in fields if x in self._fields]
    #     result = super(Ventas, self).read(real_fields, load=load)
    #     # adding fields to result
    #     [result[0].update({x: False}) for x in fields if x not in real_fields]
    #     return result


class DetalleVentas(models.Model):
    _name = 'detalle.ventas'
    _description = 'Líneas de pedido de ventas'

    venta_id = fields.Many2one('ventas', string='Venta', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio_venta = fields.Float(compute='_compute_precio_venta', string='Precio unitario')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    currency_id = fields.Many2one(related='venta_id.currency_id')
    name_venta = fields.Char(related='venta_id.name')
    # credit_note_id = fields.Many2one('credit.note', related='venta_id.credit_note_id')

    @api.depends('producto_id')
    def _compute_precio_venta(self):
        for rec in self:
            sales_price_history_ids = rec.producto_id.sales_price_history_ids.filtered(
                lambda x: x.modified_date <= rec.venta_id.fecha)
            new_price = sales_price_history_ids and sales_price_history_ids.sorted(
                key=lambda x: x.modified_date)[-1].new_price
            rec.update({'precio_venta': new_price})

    @api.depends('cantidad', 'precio_venta')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio_venta:
                rec.update({'subtotal': rec.cantidad * rec.precio_venta})

    def validate_stock(self):  # OK
        quantity_product = self.env['movimientos'].search([('producto_id', '=', self.producto_id.id)],
                                                          order='id DESC', limit=1).total
        if self.cantidad > quantity_product:
            raise ValidationError(
                f'La Cantidad solicitada para el Producto {self.producto_id.name} es de {self.cantidad} y esta excede '
                f'su stock actual -> {self.producto_id.stock}\nAsegúrese de tener el inventario actualizado para '
                f'registrar la venta correctamente.')

    def update_validate_stock(self):  # OK
        movements_model = self.env['movimientos']
        current_movement = movements_model.search([('detalle_venta_ids', '=', self.id)])
        quantity_product = (movements_model.search([('producto_id', '=', self.producto_id.id)],
                                                   order='create_date DESC', limit=2) - current_movement).total
        if self.cantidad > quantity_product:
            raise ValidationError(
                f'La Cantidad solicitada para el Producto {self.producto_id.name} es de {self.cantidad} y esta excede '
                f'su stock actual -> {self.producto_id.stock}\nAsegúrese de tener el inventario actualizado para '
                f'registrar la venta correctamente.')

    def create_movement(self):  # OK
        movements_model = self.env['movimientos']
        last_movement = movements_model.search([('producto_id', '=', self.producto_id.id)], order='id DESC', limit=1)
        movements_model.create({
            'detalle_venta_ids': [(4, self.id, False)],
            'tipo': 'out',
            'user_id': self.venta_id.user_id.id,
            'fecha': datetime.now(),
            'producto_id': self.producto_id.id,
            'cantidad': self.cantidad,
            'total': last_movement.total - self.cantidad,
        })

    def update_movement(self):  # OK
        movements_model = self.env['movimientos']
        movement = movements_model.search([('detalle_venta_ids', '=', self.id)])
        last_movement = movements_model.search([('producto_id', '=', self.producto_id.id)],
                                               order='create_date DESC', limit=2) - movement
        movement.update({
            'fecha': datetime.now(),
            'producto_id': self.producto_id,
            'cantidad': self.cantidad,
            'total': last_movement.total - self.cantidad
        })

    def action_set_confirm(self):
        self.ensure_one()
        self.validate_stock()
        self.create_movement()

    def action_set_cancel(self):
        self.ensure_one()
        movements_model = self.env['movimientos']
        last_movement = movements_model.search([('producto_id', '=', self.producto_id.id)], order='id DESC',
                                               limit=1)
        movements_model.create({
            'detalle_venta_ids': [(4, self.id), False],
            'tipo': 'in',
            'user_id': self.venta_id.user_id.id,
            'fecha': datetime.now(),
            'producto_id': self.producto_id.id,
            'cantidad': self.cantidad,
            'total': last_movement.total + self.cantidad,
        })

    # @api.model
    # def create(self, values):  # OK
    #     rec = super(DetalleVentas, self).create(values)
    #     rec.validate_stock()
    #     rec.create_movement()
    #     return rec
    #
    # def write(self, values):  # OK
    #     rec = super(DetalleVentas, self).write(values)
    #     self.update_validate_stock()
    #     self.update_movement()
    #     return rec


class Movimientos(models.Model):
    _inherit = 'movimientos'

    detalle_venta_ids = fields.Many2many('detalle.ventas')
