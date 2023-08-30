from odoo import api, fields, models


class Producto(models.Model):
    _inherit = 'base.producto'

    sales_price_history_ids = fields.One2many(comodel_name='sales.price.history', inverse_name='product_id')

    @api.model
    def create(self, values):
        rec = super(Producto, self).create(values)
        rec.update({
            'sales_price_history_ids': [(0, 0, {
                'old_price': rec.precio_venta,
                'new_price': rec.precio_venta,
                'modified_date': fields.Date.today()
            })]
        })
        return rec

    def write(self, values):
        precio_venta = values.get('precio_venta', '')
        if precio_venta:
            values.update({
                'sales_price_history_ids': [(0, 0, {
                    'old_price': self.precio_venta,
                    'new_price': precio_venta,
                    'modified_date': fields.Date.today()
                })]
            })
        return super(Producto, self).write(values)


class SalesPriceHistory(models.Model):
    _name = 'sales.price.history'

    product_id = fields.Many2one(comodel_name='base.producto')
    old_price = fields.Monetary(string='Precio antiguo', currency_field='currency_id')
    new_price = fields.Monetary(string='Precio nuevo', currency_field='currency_id')
    modified_date = fields.Date(string='Fecha de modificación')
    currency_id = fields.Many2one(related='product_id.currency_id', store=True)
