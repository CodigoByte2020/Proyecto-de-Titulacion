from odoo import fields, models


class Producto(models.Model):
    _inherit = 'base.producto'

    categoria_id = fields.Many2one('categoria.producto', required=True, string='Categoría')


class CategoriaProducto(models.Model):
    _name = 'categoria.producto'
    _description = 'Categoría de productos'

    name = fields.Char(string='Nombre', required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
