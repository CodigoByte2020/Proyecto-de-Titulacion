import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.estructura_base.models.constantes import (
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)


class AjustesInventario(models.Model):
    _name = 'ajustes.inventario'

    name = fields.Char(string='Nombre', required=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    state = fields.Selection(STATE_SELECTION, default=PENDIENTE, string='Estado')
    detalle_ajuste_inventario_ids = fields.One2many(
        'detalle.ajustes.inventario',
        'ajuste_inventario_id',
        string='Detalles',
        states={CONFIRMADO: [('readonly', True)]}
    )
    fecha = fields.Date(default=fields.Date.today(), string='Fecha', readonly=True)

    def action_set_confirm(self):
        """
        Usado para el inventario inicial y crea registro de movimientos para cada una de sus líneas.
        Las líneas de tipo inventario modifican el total de un producto.
        Falta definir como hacer cuando queremos modificar el total de un producto en específico, si debemos
        crear un ajuste de inventario o hacerlo de una manera mas directa. ???
        """
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        for rec in self.detalle_ajuste_inventario_ids:
            self.env['movimientos'].create({
                'tipo': 'aj',
                'user_id': self.user_id.id,
                'fecha': datetime.datetime.now(),
                'producto_id': rec.producto_id.id,
                'cantidad': rec.cantidad,
                'total': rec.cantidad
            })


class DetalleAjustesInventario(models.Model):
    _name = 'detalle.ajustes.inventario'

    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    ajuste_inventario_id = fields.Many2one('ajustes.inventario', string='Ajuste inventario')

    # # FIXME: CHEKEAR LA FUNCIONALIDAD DE ESTE MÉTODO
    # def crear_movimientos(self, rec):
    #     domain = [('id', '=', rec.ajuste_inventario_id.id), ('state', '=', CONFIRMADO)]
    #     inventario = self.env['ajustes.inventario'].search(domain)
    #     if inventario:
    #         self.env['movimientos'].create({
    #             'tipo': 'aj',
    #             'user_id': inventario.user_id.id,
    #             'fecha': rec.fecha,
    #             'producto_id': rec.producto_id.id,
    #             'cantidad': rec.cantidad,
    #             'total': rec.cantidad
    #         })
    #
    # # FIXME: CHEKEAR LA FUNCIONALIDAD DE ESTE MÉTODO
    # @api.model
    # def create(self, values):
    #     rec = super(DetalleAjustesInventario, self).create(values)
    #     self.crear_movimientos(rec)
    #     return rec

    @api.constrains('cantidad')
    def _check_cantidad(self):
        for rec in self:
            if rec.cantidad < 0:
                raise ValidationError('La Cantidad debe se mayor a 0 !!!')
            elif rec.cantidad > 100:
                raise ValidationError('La Cantidad máxima permitida es 100 unidades !!!')
