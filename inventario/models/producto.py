from odoo import api, fields, models


class Producto(models.Model):
    _inherit = 'base.producto'

    categoria_id = fields.Many2one('categoria.producto', required=True, string='Categoría')
    movimiento_ids = fields.One2many('movimientos', 'producto_id')
    stock = fields.Float(string='Stock', compute='_compute_stock')

    @api.depends('movimiento_ids')
    def _compute_stock(self):
        for rec in self:
            rec.stock = self.env['movimientos'].search([('producto_id', '=', rec.id)], order='fecha DESC', limit=1).total


class CategoriaProducto(models.Model):
    _name = 'categoria.producto'
    _description = 'Categoría de productos'

    name = fields.Char(string='Nombre', required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)

