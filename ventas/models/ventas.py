from odoo import api, fields, models

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    usuario_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta')
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        string='Líneas de pedido'
    )

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(
                    self._name, sequence_date=None) or '/'
        return super(Ventas, self).create(values)

    @api.depends('detalle_ventas_ids')
    def _compute_total(self):
        for rec in self:
            total = sum(rec.detalle_ventas_ids.mapped('subtotal'))
            rec.write({'total': total})

    # for rec in self:
    #     total = 0
    #     records = self.env['ventas.detalle.ventas'].search([('venta_id', '=', rec.id)])
    #     for i in records:
    #         total = total + i.subtotal
    #     rec.write({'total': total})


class DetalleVentas(models.Model):
    _name = 'detalle.ventas'
    _description = 'Líneas de pedido de ventas'

    venta_id = fields.Many2one('ventas', string='Venta', required=True)
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio = fields.Float(related='producto_id.precio', string='Precio')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('cantidad', 'precio')
    def _compute_subtotal(self):
        for rec in self:
            if rec.cantidad and rec.precio:
                rec.write({'subtotal': rec.cantidad * rec.precio})
