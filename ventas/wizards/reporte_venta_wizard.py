from datetime import datetime, date

import pytz
from dateutil.relativedelta import relativedelta

from odoo import fields, models

MONTH_SELECTION = [
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Setiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre')
]


class ReporteVentaWizard(models.TransientModel):
    _name = 'reporte.venta.wizard'
    _description = 'Reportes de ventas'

    def _default_month(self):
        user_tz = self.env.user.tz or 'America/Lima'
        timezone = pytz.timezone(user_tz)
        current = datetime.now(timezone)
        month = current.month
        if month and len(str(month)) == 1:
            month = f'0{month}'
        return str(month)

    def _get_years(self):
        return [(str(x), x) for x in range(fields.Date.today().year, 2020, -1)]

    type_report = fields.Selection([
        ('personal', 'Por cliente'),
        ('general', 'Todos los clientes')
    ], string='Tipo de reporte', default='personal')
    document_number = fields.Char(string='Número de documento')
    range = fields.Selection([
        ('month', 'Por mes'),
        ('dates', 'Por fechas'),
    ], 'Seleccionar', default='month')
    year = fields.Selection(
        selection='_get_years', string='Año', required=True, default=lambda x: str(fields.Date.today().year))
    month = fields.Selection(MONTH_SELECTION, string='Mes', default=_default_month)
    date_from = fields.Date('Desde', default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_to = fields.Date('Hasta', default=lambda self: fields.Date.to_string(
        (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))

    def reporte_venta_pdf(self):
        detalle_ventas_model = self.env['detalle.ventas']
        domain = [('venta_id.state', '=', 'confirmed')]
        if self.type_report == 'personal':
            domain += [('venta_id.cliente_id.numero_documento', '=', self.document_number)]
        if self.range == 'dates':
            domain += [
                ('venta_id.fecha', '>=', self.date_from),
                ('venta_id.fecha', '<=', self.date_to)
            ]
            return detalle_ventas_model.search(domain)
        else:
            return detalle_ventas_model.search(domain).filtered(
                lambda x: x.venta_id.fecha.month == int(self.month) and x.venta_id.fecha.year == int(self.year))
