from datetime import datetime, date, timedelta
from itertools import groupby
from odoo import api, fields, models
from odoo.addons.estructura_base.models.constantes import (
    BORRADOR,
    CONFIRMADO,
    UTILIZADO,
    CANCELADO,
    STATE_NOTE_SELECTION
)


TYPE_CREDIT_NOTE_SELECTION = [
    ('01', 'Anulación de la operación'),
    ('02', 'Anulación por error en el RUC'),
    ('03', 'Corrección por error en la descripción'),
    ('04', 'Descuento global'),
    ('05', 'Descuento por ítem'),
    ('06', 'Devolución total'),
    ('07', 'Devolución por ítem'),
    ('08', 'Bonificación'),
    ('09', 'Disminución en el valor'),
    ('10', 'Ajustes - montos y/o fechas de pago')
]


class CreditNote(models.Model):
    _name = 'credit.note'

    name = fields.Char(string='Número', default='/', copy=False)
    detalle_ventas_ids = fields.Many2many(comodel_name='detalle.ventas', string='Facturas')
    cliente_id = fields.Many2one('base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)])
    document_number = fields.Char(related='cliente_id.numero_documento', readonly=True)
    fecha = fields.Date(default=fields.Date.today(), readonly=True, string='Fecha')
    motivo = fields.Text(string='Motivo')
    type_credit_note = fields.Selection(TYPE_CREDIT_NOTE_SELECTION, required=True, string='Tipo de nota de crédito')
    amount_untaxed = fields.Float(compute='_compute_total', store=True, string='Ope. Gravadas')
    amount_tax = fields.Float(compute='_compute_total', store=True, string='IGV 18%')
    total = fields.Float(compute='_compute_total', store=True, string='Importe Total')
    comentarios = fields.Text(string='Comentarios')
    state = fields.Selection(STATE_NOTE_SELECTION, default=BORRADOR, string='Estado')
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)

    @api.depends('detalle_ventas_ids.subtotal')
    def _compute_total(self):
        for move in self:
            total = sum(move.detalle_ventas_ids.mapped('subtotal'))
            amount_tax = total * 0.18
            move.update({
                'amount_untaxed': total - amount_tax,
                'amount_tax': amount_tax,
                'total': total
            })

    def _get_ventas(self):
        range_days = self._get_range_days()
        return self.env['ventas'].search([
            ('cliente_id.numero_documento', '=', self.document_number),
            ('fecha', 'in', range_days),
            ('credit_note_id', '=', False)
        ]).sorted(key=lambda x: x.fecha, reverse=True)

    @staticmethod
    def _get_range_days():
        today = datetime.date(datetime.today())
        range_date = []
        day = 0
        while len(range_date) <= 15:
            date = today - timedelta(days=day)
            if int(date.strftime('%w')) in range(1, 6):
                range_date.append(date)
            day += 1
        return range_date

    def load_invoices(self):
        ventas = self._get_ventas()
        view_id = self.env.ref('ventas.credit_note_wizard_view_form').id
        return {
            'name': 'Buscar Facturas',
            'type': 'ir.actions.act_window',
            'res_model': 'credit.note.wizard',
            'view_mode': 'form',
            'view_id': view_id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_credit_note_id': self.id,
                'default_venta_ids': [(4, venta.id, 0) for venta in ventas]
            }
        }

    @api.model
    def create(self, values):
        if values.get('name', '/') == '/':
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    self._name, sequence_date=None) or '/'
            else:
                values['name'] = self.env['ir.sequence'].next_by_code(self._name, sequence_date=None) or '/'
        return super(CreditNote, self).create(values)

    def action_set_confirm(self):
        self.update({'state': CONFIRMADO})
        sorted_sales_detail = self.detalle_ventas_ids.sorted(key=lambda x: x.producto_id.id)
        grouped_sales_detail = [(key, list(group)) for key, group in
                                groupby(sorted_sales_detail, key=lambda x: x.producto_id.id)]

        movements_model = self.env['movimientos']
        for product_id, values in grouped_sales_detail:
            last_movement = movements_model.search([('producto_id', '=', product_id)], order='create_date DESC',
                                                   limit=1)
            quantity = sum(x.cantidad for x in values)
            movements_model.create({
                'detalle_venta_id': [(4, sale_detail.id) for sale_detail in values],
                'tipo': 'in',
                'user_id': self.user_id.id,
                'fecha': datetime.now(),
                'producto_id': product_id,
                'cantidad': quantity,
                'total': last_movement.total + quantity,
            })

    def action_cancel(self):
        self.update({'state': CANCELADO})


class DetalleVentas(models.Model):
    _inherit = 'detalle.ventas'

    name_venta = fields.Char(related='venta_id.name')
