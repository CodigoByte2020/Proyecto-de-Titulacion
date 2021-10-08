from odoo import api, fields, models


class Compras(models.Model):
    _name = 'compras'
    _description = 'Registro de compras'

    name = fields.Char(string='Número', default='/', copy=False)
    proveedor_id = fields.Many2one('base.persona', string='Proveedor', required=True, domain=[('rango_proveedor', '=', 1)])
    usuario_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha')
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_compras_ids = fields.One2many(
        'detalle.compras',
        'compra_id',
        string='Líneas de compra'
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
    subtotal = fields.Float(string='Subtotal')
