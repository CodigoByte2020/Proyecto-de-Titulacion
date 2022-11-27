import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError

TIPO_DOCUMENTO_SELECTION = [
    ('dni', 'DOCUMENTO NACIONAL DE IDENTIDAD'),
    ('ce', 'CARNET DE EXTRANJERÍA'),
    ('ruc', 'REGISTRO ÚNICO DE CONTRIBUYENTES')
]

dni_validator = re.compile(r'^\d{8}$')
ce_validator = re.compile(r'^\d{9}$')
ruc_validator = re.compile(r'^\d{11}$')


class Persona(models.Model):
    _name = 'base.persona'
    _description = 'Clientes y Proveedores'

    name = fields.Char(string='Nombre', required=True)
    tipo_documento = fields.Selection(TIPO_DOCUMENTO_SELECTION, string='Tipo de Documento', required=True)
    numero_documento = fields.Char(string='Número de documento', required=True)
    direccion = fields.Text(string='Dirección')
    celular = fields.Char(string='Celular')
    email = fields.Char(string='Email')
    rango_cliente = fields.Integer(default=0)
    rango_proveedor = fields.Integer(default=0)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    _sql_constraints = [
        ('name_uniq', 'unique(numero_documento)', 'Ya existe un Cliente con el Número de documento ingresado !!!'),
    ]

    @api.onchange('tipo_documento')
    def _onchange_tipo_documento(self):
        if self.tipo_documento:
            return {'value': {'numero_documento': False}}

    @api.constrains('numero_documento')
    def _check_numero_documento(self):
        for rec in self:
            if rec.tipo_documento == 'dni' and not dni_validator.match(rec.numero_documento):
                raise ValidationError('El Número de documento debe tener 8 números.')
            elif rec.tipo_documento == 'ce' and not ce_validator.match(rec.numero_documento):
                raise ValidationError('El Número de documento debe tener 9 números.')
            elif rec.tipo_documento == 'ruc' and not ruc_validator.match(rec.numero_documento):
                raise ValidationError('El Número de documento debe tener 11 números.')

    def name_get(self):
        return [(rec.id, f'{rec.name} - {rec.numero_documento}')for rec in self]
