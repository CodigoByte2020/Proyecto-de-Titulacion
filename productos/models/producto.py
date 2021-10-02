from odoo import fields, models


class Producto(models.Model):
    _name = 'productos.producto'
    _description = 'Productos'

    name = fields.Char(string='Nombre', required=True)
    categoria_id = fields.Many2one('productos.categoria.producto', string='Categoría')
    precio = fields.Float(string='Precio')
    stock = fields.Integer(string='Stock')
    comentarios = fields.Text(string='Comentarios')
