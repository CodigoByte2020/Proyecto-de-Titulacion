from odoo import fields, models


class Producto(models.Model):
    _inherit = 'base.producto'

    categoria_id = fields.Many2one('inventario.categoria.producto', string='Categoría')


class CategoriaProducto(models.Model):
    _name = 'inventario.categoria.producto'
    _description = 'Categoría de productos'

    name = fields.Char(string='Nombre', required=True)
