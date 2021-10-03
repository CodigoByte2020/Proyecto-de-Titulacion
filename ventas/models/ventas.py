from odoo import api, fields, models

FORMA_PAGO_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]


class Ventas(models.Model):
    _name = 'ventas.ventas'
    _description = 'Ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    cliente_id = fields.Many2one('ventas.cliente', string='Cliente', required=True)
    usuario_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Usuario', readonly=True)
    fecha = fields.Datetime(string='Fecha')
    forma_pago = fields.Selection(FORMA_PAGO_SELECTION, string='Forma de pago')
    total = fields.Float(string='Total')
    detalle_ventas_ids = fields.One2many(
        'ventas.detalle.ventas',
        'venta_id',
        string='Líneas de pedido'
    )
    comentarios = fields.Text(string='Comentarios')

    # @api.depends('detalle_ventas_ids')
    # def _compute_total(self):
    #     for rec in self:
    #         total = sum(rec.detalle_ventas_ids.mapped('subtotal'))
    #         rec.write({'total': total})

        # for rec in self:
        #     total = 0
        #     records = self.env['ventas.detalle.ventas'].search([('venta_id', '=', rec.id)])
        #     for i in records:
        #         total = total + i.subtotal
        #     rec.update({'total': total})

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    self._name, sequence_date=None) or '/'
            return super(Ventas, self).create(vals)


class DetalleVentas(models.Model):
    _name = 'ventas.detalle.ventas'
    _description = 'Detalle de ventas'

    venta_id = fields.Many2one('ventas.ventas', string='Venta', required=True)
    producto_id = fields.Many2one('productos.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio = fields.Float(related='producto_id.precio', string='Precio')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal')

    @api.depends('cantidad', 'precio')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio:
                rec.update({'subtotal': rec.cantidad * rec.precio})
            # return {
            #     'value': {
            #         'subtotal': self.cantidad * self.precio
            #     }
            # }
