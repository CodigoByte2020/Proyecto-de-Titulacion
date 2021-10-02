from odoo import fields, models

TIPO_DOCUMENTO_SELECTION = [
    ('dni', 'DOCUMENTO NACIONAL DE IDENTIDAD (DNI)'),
    ('ce', 'CARNET DE EXTRANJERÍA')
]


class Cliente(models.Model):
    _name = 'ventas.cliente'
    _description = 'Clientes'

    name = fields.Char(string='Nombre', required=True)
    tipo_documento = fields.Selection(TIPO_DOCUMENTO_SELECTION, string='Tipo de Documento')
    numero_documento = fields.Char(string='Número de documento')
    edad = fields.Integer(string='Edad')
    direccion = fields.Text(string='Dirección')
    celular = fields.Char(string='Celular')
    email = fields.Char(string='Email')
