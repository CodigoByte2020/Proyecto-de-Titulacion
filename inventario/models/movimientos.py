from odoo import api, fields, models
from odoo.addons.estructura_base.models.constantes import CONFIRMADO

TIPO_MOVIMIENTO_SELECTION = [
    ('in', 'Entrada'),
    ('out', 'Salida'),
    ('aj', 'Ajuste')
]


class Movimientos(models.Model):
    _name = 'movimientos'

    tipo = fields.Selection(TIPO_MOVIMIENTO_SELECTION, string='Tipo')
    user_id = fields.Many2one('res.users', string='Responsable', readonly=True)
    fecha = fields.Date(string='Fecha')
    producto_id = fields.Many2one('base.producto')
    cantidad = fields.Float(string='Cantidad')
    total = fields.Float(string='Total')

    @api.model
    def _cron_movimientos(self, fecha):
        if fecha is None:
            fecha = fields.Date.context_today(self)
        else:
            fecha = fields.Date.from_string(fecha)

        query = """
            select v.user_id, v.fecha, dv.producto_id, dv.cantidad from ventas as v
                inner join detalle_ventas as dv on v.id = dv.venta_id
                where v.fecha = %s and state = %s
        """

        self._cr.execute(query, (fecha, CONFIRMADO))
        records = self._cr.dictfetchall()
        lista = list()
        for rec in records:
            lista += [(0, 0, {
                        'tipo': 'aj',
                        'user_id': rec['user_id'],
                        'fecha': rec['fecha'],
                        'producto_id': rec['producto_id'],
                        'cantidad': rec['cantidad']
            })]
        self.create(lista)
