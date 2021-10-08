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
    direccion = fields.Text(string='Dirección')
    celular = fields.Char(string='Celular')
    email = fields.Char(string='Email')
    rango_cliente = fields.Integer(default=0)
    rango_proveedor = fields.Integer(default=0)
