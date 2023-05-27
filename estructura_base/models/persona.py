import logging
import re
import requests
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

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

    # COMPROBAR QUE LOS CLIENTES SIN NOMBRE NO GENEREN PROBLEMAS EN LOS DEMÁS PROCESOS
    name = fields.Char(string='Nombre')
    tipo_documento = fields.Selection(TIPO_DOCUMENTO_SELECTION, string='Tipo de Documento', required=True)
    numero_documento = fields.Char(string='Número de documento', required=True)
    direccion = fields.Text(string='Dirección')
    celular = fields.Char(string='Celular')
    email = fields.Char(string='Email')
    rango_cliente = fields.Integer(default=0)
    rango_proveedor = fields.Integer(default=0)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    estado = fields.Char(string='Estado')
    condicion = fields.Char(string='Condición')

    _sql_constraints = [
        ('name_uniq', 'unique(numero_documento)', 'Ya existe un Cliente con el Número de documento ingresado !!!'),
    ]

    @api.onchange('tipo_documento')
    def _onchange_tipo_documento(self):
        if self.tipo_documento:
            return {'value': {'numero_documento': False}}

    @api.onchange('numero_documento')
    def _onchange_numero_documento(self):
        if self.numero_documento:
            if self.tipo_documento == 'dni' and not dni_validator.match(self.numero_documento):
                raise ValidationError('El Número de documento debe tener 8 números.')
            elif self.tipo_documento == 'ce' and not ce_validator.match(self.numero_documento):
                raise ValidationError('El Número de documento debe tener 9 números.')
            elif self.tipo_documento == 'ruc' and not ruc_validator.match(self.numero_documento):
                raise ValidationError('El Número de documento debe tener 11 números.')

    def name_get(self):
        return [(rec.id, f'{rec.name} - {rec.numero_documento}') for rec in self]

    def consult_data(self):
        url = f'https://api.apis.net.pe/v1/{self.tipo_documento}'
        args = {'numero': self.numero_documento}
        # TRY: CÓDIGO SUCEPTIBLE A ERROR
        try:
            response = requests.get(url=url, params=args)
        # CAPTURAMOS LA EXEPCIÓN
        except requests.exceptions.RequestException as e:
            _logger.info(f'*********************** LA CONEXIÓN FALLO *********************** {e}')
            raise ValidationError('La conexión falló al consultar datos.')
        # SI NO OCURRE NINGUNA EXEPCIÓN
        else:
            if response.status_code == 200:
                response_json = response.json()
                nombre = response_json.get('nombre', '')
                direccion = response_json.get('direccion', '')
                provincia = response_json.get('provincia', '')
                estado = response_json.get('estado', '')
                condicion = response_json.get('condicion', '')
                self.update({
                    'name': nombre,
                    'direccion': direccion and provincia and f'{direccion}\n{provincia} - PERÚ',
                    'estado': estado,
                    'condicion': condicion
                })
            elif response.status_code == 422:
                raise ValidationError(f'El Número de documento {self.numero_documento} no cumple con las reglas de '
                                      f'validación')
            elif response.status_code == 404:
                raise ValidationError(f'El Número de documento {self.numero_documento} no existe')
