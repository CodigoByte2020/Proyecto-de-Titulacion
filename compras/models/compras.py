from odoo import api, fields, models

from odoo.addons.estructura_base.models.constantes import (
    BORRADOR,
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)


class Compras(models.Model):
    _name = 'compras'
    _description = 'Registro de compras'

    name = fields.Char(string='Número', default='/', copy=False)
    state = fields.Selection(STATE_SELECTION, default=BORRADOR, string='Estado')
    proveedor_id = fields.Many2one(
        'base.persona', string='Proveedor', required=True, domain=[('rango_proveedor', '=', 1)],
        states={CONFIRMADO: [('readonly', True)]}
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha',
                            states={CONFIRMADO: [('readonly', True)]})
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_compras_ids = fields.One2many(
        'detalle.compras',
        'compra_id',
        string='Líneas de compra',
        states={CONFIRMADO: [('readonly', True)]}
    )

    def action_set_confirm(self):
        '''
        Busca el último movimiento registrado que pertenezca al producto en cuestión, para calcular el total.
        :return:
        '''
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        detalle_compras = self.env['detalle.compras'].search([('compra_id', '=', self.id)])
        if detalle_compras:
            for rec in detalle_compras:
                domain = [('producto_id', '=', rec.producto_id.id)]
                movimiento_anterior = self.env['movimientos'].search(domain, order='create_date DESC', limit=1)
                movimiento = {
                    'tipo': 'in',
                    'user_id': self.user_id.id,
                    'fecha': self.fecha,
                    'producto_id': rec.producto_id.id,
                    'cantidad': rec.cantidad,
                    'total': rec.cantidad + movimiento_anterior.total if movimiento_anterior else rec.cantidad
                }
                self.env['movimientos'].create(movimiento)

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(
                    self._name, sequence_date=None) or '/'
            values['state'] = PENDIENTE
        return super(Compras, self).create(values)

    @api.depends('detalle_compras_ids')
    def _compute_total(self):
        for rec in self:
            total = sum(rec.detalle_compras_ids.mapped('subtotal'))
            rec.write({'total': total})


class DetalleCompras(models.Model):
    _name = 'detalle.compras'
    _description = 'Líneas de pedido de compras'

    compra_id = fields.Many2one('compras', string='Compra', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)
    precio_compra = fields.Float(related='producto_id.precio_compra', string='Precio')

    @api.depends('cantidad', 'precio_compra')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio_compra:
                rec.write({'subtotal': rec.cantidad * rec.precio_compra})

    # def crear_movimientos(self, rec):
    #     compra = self.env['compras'].search([('id', '=', rec.compra_id.id), ('state', '=', CONFIRMADO)])
    #     if compra:
    #         domain = [('producto_id', '=', rec.producto_id.id), ('tipo', 'in', ['in', 'aj'])]
    #         movimiento_anterior = self.env['movimientos'].search(domain, order='create_date DESC', limit=1)
    #         movimiento = {
    #             'tipo': 'in',
    #             'user_id': compra.user_id.id,
    #             'fecha': compra.fecha,
    #             'producto_id': rec.producto_id.id,
    #             'cantidad': rec.cantidad,
    #             'total': rec.cantidad + movimiento_anterior.total if movimiento_anterior else rec.cantidad
    #         }
    #         self.env['movimientos'].create(movimiento)
    #
    # @api.model
    # def create(self, values):
    #      rec = super(DetalleCompras, self).create(values)
    #      self.crear_movimientos(rec)
    #      return rec
        