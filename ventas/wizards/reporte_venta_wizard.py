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
    ], string='Report type', default='personal')
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

    # TODO: Falta implementar
    def button_export_pdf(self):
        pass
