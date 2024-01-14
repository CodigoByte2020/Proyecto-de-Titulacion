import base64
import io
from datetime import datetime, date
from itertools import groupby

import pytz
import pandas as pd
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

    @staticmethod
    def _get_years():
        return [(str(year), year) for year in range(fields.Date.today().year, 2020, -1)]

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
    report_number = fields.Integer(default=0)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def get_report_number(self):
        self.report_number += 1
        return self.report_number

    def _get_sales_detail(self):
        detalle_ventas_model = self.env['detalle.ventas']
        domain, sales_detail = [], []
        if self.type_report == 'personal':
            domain.extend([('venta_id.cliente_id.numero_documento', '=', self.document_number)])
        if self.range == 'dates':
            domain.extend([('venta_id.fecha', '>=', self.date_from), ('venta_id.fecha', '<=', self.date_to)])
            sales_detail = detalle_ventas_model.search(domain)
        elif self.range == 'month':
            sales_detail = detalle_ventas_model.search(domain).filtered(
                lambda x: x.venta_id.fecha.month == int(self.month) and x.venta_id.fecha.year == int(self.year))
        sorted_sales_detail = sales_detail.sorted(key=lambda x: x.venta_id.cliente_id.name)
        grouped_sales_detail = [{key: list(group)} for key, group in
                                groupby(sorted_sales_detail, key=lambda x: x.venta_id.cliente_id.name)]
        return grouped_sales_detail

    @staticmethod
    def _get_totals(sales_detail):
        total = sum(map(lambda x: x.subtotal, sales_detail))
        amount_tax = total * 0.18
        subtotal = total - amount_tax
        return {'total': total, 'amount_tax': amount_tax, 'subtotal': subtotal}

    # FIXME: REVISAR ESTE MÉTODO
    def xlsx_sale_repor(self):
        sales_detail = self._get_sales_detail()
        data = [{
            'user_id': line.venta_id.user_id.name,
            'tipo_venta': line.venta_id.tipo_venta,
            'fecha': line.venta_id.fecha,
            'product_id': line.producto_id.name,
            'cantidad': line.cantidad,
            'precio_venta': line.precio_venta,
            'subtotal': line.subtotal
        } for line in sales_detail]
        # CREANDO DATAFRAMES PARA PANDAS
        df = pd.DataFrame(data)
        # CONVERTIR A EXCEL EN MEMORIA
        xlsx_bytes = io.BytesIO()
        df.to_excel(xlsx_bytes, index=False)
        xlsx_bytes.seek(0)
        xls_data = xlsx_bytes.getvalue()
        result = base64.b64encode(xls_data)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        attachment = self.env['ir.attachment'].create({
            'name': 'Reporte XLSX de Venta',
            'datas': result
        })
        download_url = '/web/content/' + str(attachment.id) + '?download=true'
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }

    def xlsx_sale_report(self):
        sales_details = self._get_sales_detail()
        # CREAR UN ESCRITOR EXCEL
        # xlsx_bytes = io.BytesIO()
        with pd.ExcelWriter('reporte_ventas.xlsx', engine='xlsxwriter') as excel_writer:
            for sales_detail in sales_details:
                client_name = list(sales_detail.keys())[0]
                client_values = list(sales_detail.values())[0]
                data = [{
                    'user_id': line.venta_id.user_id.name,
                    'tipo_venta': line.venta_id.tipo_venta,
                    'fecha': line.venta_id.fecha,
                    'product_id': line.producto_id.name,
                    'cantidad': line.cantidad,
                    'precio_venta': line.precio_venta,
                    'subtotal': line.subtotal
                } for line in client_values]
                # CREAR DATAFRAMES PARA PANDAS
                df = pd.DataFrame(data)
                # ESCRIBIR EL DATAFRAME EN EL EXCEL EN MEMORIA
                # df.to_excel(excel_writer, sheet_name=client_name, index=False)
                xlsx_bytes = io.BytesIO()
                df.to_excel(xlsx_bytes, sheet_name=client_name, index=False)
                print('V')

        # OBTENER LOS DATOS DEL EXCEL EN MEMORIA
        # xlsx_bytes = io.BytesIO()
        xlsx_bytes.seek(0)
        xls_data = xlsx_bytes.getvalue()  # FIXME: ERROR
        # CONVERTIR LOS DATOS A BASE64 PARA ALMACENARLO EN UN ARCHIVO DE IR.ATTACHMENT
        result = base64.b64encode(xls_data)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # GUARDAR EL ARCHIVO EN IR.ATTACHMENT
        attachment = self.env['ir.attachment'].create({
            'name': 'Reporte XLSX de Venta',
            'datas': result
        })

        # OBTENER LA URL DE DESCARGA DEL ARCHIVO
        download_url = '/web/content/' + str(attachment.id) + '?download=true'

        # REDIRECCIONAR AL USUARIO A LA URL DE DESCARGA
        return {
            "type": "ir.actions.act_url",
            "url": str(base_url) + str(download_url),
            "target": "new",
        }
