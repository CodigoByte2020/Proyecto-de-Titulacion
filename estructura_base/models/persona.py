from odoo import api, fields, models

TIPO_DOCUMENTO_SELECTION = [
    ('dni', 'DOCUMENTO NACIONAL DE IDENTIDAD (DNI)'),
    ('ce', 'CARNET DE EXTRANJERÍA')
]


class Persona(models.Model):
    _name = 'base.persona'
    _description = 'Clientes y Proveedores'

    name = fields.Char(string='Nombre', required=True)
    tipo_documento = fields.Selection(TIPO_DOCUMENTO_SELECTION, string='Tipo de Documento')
    numero_documento = fields.Char(string='Número de documento')
    edad = fields.Integer(string='Edad')
    direccion = fields.Text(string='Dirección')
    celular = fields.Char(string='Celular')
    email = fields.Char(string='Email')


# class CreditoCliente(models.Model):
#     _name = 'angita_base.credito.cliente'
#     _description = 'Crédito de clientes'
#
#     name = fields.Char(string='Número', default='/', copy=False)
#     cliente_id = fields.Many2one('ventas.cliente', string='Cliente', required=True)
#     limite_credito = fields.Float(string='Límite de crédito')
#     deuda = fields.Float(string='Deuda')
#     estado = fields.Selection(STATE_DEUDA_SELECTION, string='Estado')
#     comentario = fields.Text(string='Comentario')
#     pago_credito_clientes_ids = fields.One2many(
#         'ventas.pago.credito.cliente',
#         'credito_cliente_id',
#         string='Pagos de crédito'
#     )
#
#     @api.model
#     def create(self, vals):
#         if vals.get('name', '/') == '/':
#             if 'company_id' in vals:
#                 vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
#                     self._name, sequence_date=None) or '/'
#             else:
#                 vals['name'] = self.env['ir.sequence'].next_by_code(
#                     self._name, sequence_date=None) or '/'
#             return super(CreditoCliente, self).create(vals)
#
#
# class PagoCreditoCliente(models.Model):
#     _name = 'ventas.pago.credito.cliente'
#     _description = 'Registro de pagos de crédito de clientes'
#
#     name = fields.Char(string='Número', default='/', copy=False)
#     credito_cliente_id = fields.Many2one('ventas.credito.cliente', string='Cliente', required=True)
#     monto = fields.Float(string='Monto')
#     fecha_pago = fields.Date(string='Fecha de pago')
#
#     @api.model
#     def create(self, vals):
#         if vals.get('name', '/') == '/':
#             if 'company_id' in vals:
#                 vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
#                     self._name, sequence_date=None) or '/'
#             else:
#                 vals['name'] = self.env['ir.sequence'].next_by_code(
#                     self._name, sequence_date=None) or '/'
#             return super(PagoCreditoCliente, self).create(vals)
