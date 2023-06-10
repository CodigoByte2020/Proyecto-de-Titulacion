from odoo import fields, models

UNIDAD_MEDIDA_SELECTION = [
    ('unit', 'Unidad'),
    ('kg', 'Kg')
]


class Producto(models.Model):
    _name = 'base.producto'
    _inherit = 'image.mixin'
    _description = 'Productos'

    name = fields.Char(string='Nombre', required=True)
    # precio_compra = fields.Float(string='Precio de compra')
    precio_venta = fields.Float(string='Precio de venta', required=True, group_operator=False)
    comentario = fields.Text(string='Comentario',
                             help='Utilize este campo para especificar detalles extras del producto.')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    unidad_medida = fields.Selection(selection=UNIDAD_MEDIDA_SELECTION, string='Unidad de medida',
                                     required=True)
    code = fields.Char(string='Código', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'El Nombre ya existe !'),
    ]
