{
    'name': 'Ventas',
    'summary': 'Módulo de Ventas',
    'description': 'Módulo para la gestión de ventas.',
    'author': 'Contreras Pumamango Gianmarco - gmcontrpuma@gmail.com',
    'website': 'https://github.com/CodigoByte2020',
    'category': 'Tools',
    'version': '13.0.0.0.1',
    'depends': [
        'inventario'
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/paperformat.xml',
        'security/ir.model.access.csv',
        'views/ventas_menus_views.xml',
        'views/ventas_views.xml',
        'views/cliente_views.xml',
        'views/credito_cliente_views.xml',
        'views/movimientos_credito_cliente_views.xml',
        'views/credito_alerta_views.xml',
        # 'views/impuestos_views.xml',
        'reports/reporte_venta.xml',
        'wizards/reporte_venta_wizard_views.xml'
    ],
    'installable': True,
}
