from odoo.addons.estructura_base.models.constantes import CONFIRMADO, UTILIZADO
from odoo import fields, models


class CreditNoteWizard(models.TransientModel):
    _name = 'credit.note.wizard'

    venta_ids = fields.Many2many(comodel_name='ventas', string='Facturas')
    credit_note_id = fields.Many2one('credit.note')

    # TODO:
    #  - UNA LÍNEA DE DETALLE DE VENTA PUEDE ESTAR EN VARIAS NOTAS DE CRÉDITO EN ESTADO BORRADOR, PERO NO EN ESTADO
    #    CONFIRMADO O UTILIZADO.
    def load_sale_details(self):
        credit_note_model = self.env['credit.note']
        confirmed_credit_note = credit_note_model.search([('state', 'in', (CONFIRMADO, UTILIZADO))])
        detalle_ventas_ids = self.env['detalle.ventas'].search([
            ('venta_id', 'in', self.venta_ids.ids),
            ('id', 'not in', confirmed_credit_note.detalle_ventas_ids.ids)
        ]).sorted(key=lambda x: x.venta_id.id, reverse=True)
        self.credit_note_id.update({'detalle_ventas_ids': [(6, 0, detalle_ventas_ids.ids)]})
