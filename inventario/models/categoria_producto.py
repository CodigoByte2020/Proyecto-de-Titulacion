from odoo import fields, models


class CategoriaProducto(models.Model):
    _name = 'base.categoria.producto'
    _description = 'Categoría de productos'

    name = fields.Char(string='Nombre', required=True)