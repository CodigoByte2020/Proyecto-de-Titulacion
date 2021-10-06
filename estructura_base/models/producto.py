from odoo import fields, models


class Producto(models.Model):
    _name = 'base.producto'
    _description = 'Productos'

    name = fields.Char(string='Nombre', required=True)
    precio = fields.Float(string='Precio')
    comentario = fields.Text(string='Comentario')
