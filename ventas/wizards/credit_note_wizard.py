from odoo import fields, models


class CreditNoteWizard(models.TransientModel):
    _name = 'credit.note.wizard'

    venta_ids = fields.Many2many(comodel_name='ventas', string='Facturas')
    credit_note_id = fields.Many2one('credit.note')

    def load_sale_details(self):
        detalle_ventas_ids = self.env['detalle.ventas'].search([('venta_id', 'in', self.venta_ids.ids)])\
            .sorted(key=lambda x: x.venta_id.id, reverse=True)
        credit_note_id = self.env['credit.note'].browse(self.credit_note_id.id)
        credit_note_id.update({'detalle_ventas_ids': [(6, 0, detalle_ventas_ids.ids)]})
