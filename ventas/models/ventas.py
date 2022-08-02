from odoo import api, fields, models
from odoo.exceptions import ValidationError
from pprint import pprint

from odoo.addons.estructura_base.models.constantes import (
    BORRADOR,
    PENDIENTE,
    CONFIRMADO,
    STATE_SELECTION
)

TIPO_VENTA_SELECTION = [
    ('contado', 'Contado'),
    ('credito', 'Crédito')
]

''' Orden de los metodos y su ejecución:
1. Método create o write del padre
2. Método create o write del hijo
3. Método en cuestión que ha sido llamado

Al eliminar un registro de One2many, por defecto odoo usa (2, id, 0), y este lo elimina de la base de datos.
El (6, 0, ids) es para campos Many2many

Cuando agregamos un registro en un One2many primero ejecuta el comando (4, id, 0), luego el comando (0, 0, values)
Primero ejecuta el write del padre y luego el create del hijo

Primero se ejecutan los métodos del padre y luego el método del hijo
'''


class Ventas(models.Model):
    _name = 'ventas'
    _description = 'Registro de ventas'

    name = fields.Char(string='Número', default='/', copy=False)
    state = fields.Selection(STATE_SELECTION, default=BORRADOR, string='Estado')
    cliente_id = fields.Many2one(
        'base.persona', string='Cliente', required=True, domain=[('rango_cliente', '=', 1)],
        states={CONFIRMADO: [('readonly', True)]}
    )
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user.id, string='Responsable', readonly=True)
    tipo_venta = fields.Selection(
        TIPO_VENTA_SELECTION, default='contado', required=True, string='Tipo de venta',
        states={CONFIRMADO: [('readonly', True)]}
    )
    fecha = fields.Datetime(default=lambda self: fields.Datetime.now(), string='Fecha',
                            states={CONFIRMADO: [('readonly', True)]})
    total = fields.Float(compute='_compute_total', store=True, string='Total')
    comentario = fields.Text(string='Comentario')
    detalle_ventas_ids = fields.One2many(
        'detalle.ventas',
        'venta_id',
        states={CONFIRMADO: [('readonly', True)]},
        string='Líneas de pedido'
    )
    hobby_ids = fields.Many2many('hobby', string='Hobbies')

    def action_set_confirm(self):
        '''
        Busca el último movimiento registrado que pertenezca al producto en cuestión, para calcular el total.
        :return:
        '''
        self.ensure_one()
        self.write({'state': CONFIRMADO})
        detalle_ventas = self.env['detalle.ventas'].search([('venta_id', '=', self.id)])
        if detalle_ventas:
            for rec in detalle_ventas:
                domain = [('producto_id', '=', rec.producto_id.id)]
                movimiento_anterior = self.env['movimientos'].search(domain, order='create_date DESC', limit=1)
                if movimiento_anterior:
                    movimiento_inventario = {
                        'tipo': 'out',
                        'user_id': self.user_id.id,
                        'fecha': self.fecha,
                        'producto_id': rec.producto_id.id,
                        'cantidad': rec.cantidad,
                        'total': movimiento_anterior.total - rec.cantidad
                    }
                    if self.tipo_venta == 'credito':
                        movimiento_credito_cliente = {
                            'credito_cliente_id': self.cliente_id.id,
                            'tipo': 'sale',
                            'fecha': self.fecha,
                            'producto_id': rec.producto_id.id,
                            'cantidad': rec.cantidad,
                            'precio': rec.precio_venta,
                            'monto': rec.subtotal,
                            'deuda': self.id,
                            'user_id': self.user_id.id
                        }
                else:
                    raise ValidationError(
                        'No se ha registrado ningúna compra o ajuste de inventario correspondiente al producto {}'
                        .format(rec.producto_id.name)
                    )
                self.env['movimientos'].create(movimiento_inventario)

    # @api.model
    # def create(self, values):
    #     if values.get('name', '/') == '/':
    #         if 'company_id' in values:
    #             values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
    #                 self._name, sequence_date=None) or '/'
    #         else:
    #             values['name'] = self.env['ir.sequence'].next_by_code(
    #                 self._name, sequence_date=None) or '/'
    #     values['state'] = PENDIENTE
    #     return super(Ventas, self).create(values)

    def practicando(self):
        self.create({
            'cliente_id': 1,
            'tipo_venta': 'contado',
            'detalle_ventas_ids': [
                (0, 0, {'producto_id': 2}),
                (0, 0, {'producto_id': 3}),
                (0, 0, {'producto_id': 4})
            ]
        })

    '''
        (1, id, values)
        Se llama al método write del padre, pasandole la tupla con el value dict.
        Luego se llama al método write del hijo, una vez por registro, pasandole el value dict correspondiente.
        Primero ejecuta el comando (4, id, 0) luego el comando (1, id, values).
        * Si lo hicieramos con el método tradicional se llamaría al método write del hijo una vez por cada valor del 
        value dict.
    '''
    def special_command1(self):
        # for rec in self.detalle_ventas_ids:
        #     rec.producto_id = 1
        #     rec.cantidad = 1000

        lista = []
        for rec in self.detalle_ventas_ids:
            lista.append((1, rec.id, {
                'producto_id': 1,
                'cantidad': 2000
            }))
        self.detalle_ventas_ids = lista

    '''
        (2, id, 0)
        Cuando ejecutamos desde el navegador, primero ejecuta el comando (4, id, 0), luego crea o elimina los registros 
        del conjunto.
        Elimina el registro de la base de datos.
    '''
    def special_command2(self):
        self.write({
            'detalle_ventas_ids': [(2, 45, 0), (2, 46, 0)]
        })

    '''
        (3, id, 0)
        Elimina el registro del conjunto, pero no lo elimina de la base de datos.
        Elimina el campo M2o al registro hijo. (desvinculación)
    '''
    def special_command3(self):
        self.write({
            'detalle_ventas_ids': [(3, 44, 0)]
        })

    '''
        (4, id, 0)
        Agrega un registro existente al conjunto.
        Agrega el campo M2o al registro hijo. (vinculación)   
    '''
    def special_command4(self):
        self.write({'detalle_ventas_ids': [(4, 40, 0), (4, 41, 0), (4, 44, 0)]})

    '''
        (5, 0, 0)
        Elimina todos los registros del conjunto.   
        Elimina el campo M2o de todos los registros hijos. (desvinculación) 
    '''
    def special_command5(self):
        self.write({'detalle_ventas_ids': [(5, 0, 0)]})

    '''
        (6, 0, ids)
        Reemplaza todos los registros existentes en el conjunto.
        Equivalente a usar el comando 5 seguido de un comando 4 para cada id en ids.
    '''
    def special_command6(self):
        ids = [1, 2, 3]
        self.write({'hobby_ids': [(6, 0, ids)]})


    @api.model
    def create(self, values):
        print('Ventas método create:')
        pprint(values)
        rec = super(Ventas, self).create(values)
        pprint(rec)
        return rec

    def write(self, values):
        print('Ventas método write:')
        pprint(values)
        rec = super(Ventas, self).write(values)
        pprint(rec)
        return rec
        # detalle_venta_ids = self.env['detalle.ventas'].search([('venta_id', '=', 2)])
        # values['detalle_ventas_ids'] = [(6, 0, detalle_venta_ids.ids)]

    # Practicando Notacion polaca
    def super_domain(self):
        domain = [('tipo_venta', '=', 'contado'), '|', ('total', '>', '10'), '&', ('cliente_id.name', '=', 'Gianmarco')]
        domain2 = [('tipo_venta', '=', 'contado'), '|', '&', ('total', '>', '10'), ('cliente_id.name', '=', 'Gianmarco')]
        domain3 = ['|', ('tipo_venta', '=', 'contado'), '&', ('total', '>', '10'), ('cliente_id.name', '=', 'Gianmarco')]
        records = self.search(domain3)

    @api.constrains('tipo_venta')
    def _check_tipo_venta(self):
        for rec in self:
            if rec.tipo_venta == 'credito':
                credito = self.env['credito.cliente'].search([('cliente_id', '=', rec.cliente_id.id)])
                if not credito:
                    raise ValidationError(f'El cliente {rec.cliente_id.name} no tiene ningun crédito registrado.')

    # Programación Imperativa: Se describe paso a paso.
    # for rec in self:
    #     total = 0
    #     records = self.env['ventas.detalle.ventas'].search([('venta_id', '=', rec.id)])
    #     for i in records:
    #         total = total + i.subtotal
    #     rec.write({'total': total})

    # Programación Declarativa: Se describe el resultado final.
    # Self es el registro de venta actual

    # @api.depends('detalle_ventas_ids')
    # def _compute_total(self):
    #     for rec in self:
    #         total = sum(rec.detalle_ventas_ids.mapped('subtotal'))
    #         rec.write({'total': total})


class DetalleVentas(models.Model):
    _name = 'detalle.ventas'
    _description = 'Líneas de pedido de ventas'

    venta_id = fields.Many2one('ventas', string='Venta')
    producto_id = fields.Many2one('base.producto', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad')
    precio_venta = fields.Float(related='producto_id.precio_venta', string='Precio')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.model
    def create(self, values):
        print('Detalle de ventas, método create:')
        pprint(values)
        rec = super(DetalleVentas, self).create(values)
        pprint(rec)
        return rec

    def write(self, values):
        print('Detalle de ventas, método write:')
        pprint(values)
        rec = super(DetalleVentas, self).write(values)
        pprint(rec)
        return rec

    # @api.depends('cantidad', 'precio_venta')
    # def _compute_subtotal(self):
    #     for rec in self:
    #         if rec.cantidad and rec.precio_venta:
    #             rec.write({'subtotal': rec.cantidad * rec.precio_venta})
