{
    'name': 'Productos',
    'summary': 'Módulo de Productos',
    'description': 'Módulo para la gestión de productos.',
    'author': 'Contreras Pumamango Gianmarco - gmcontrpuma@gmail.com',
    'website': 'https://github.com/CodigoByte2020',
    'category': 'Tools',
    'version': '13.0.0.0.1',
    'depends': [
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/producto_menus_views.xml',
        'views/productos_producto_views.xml',
        'views/productos_categoria_producto_views.xml',
    ],
    'installable': True,
}
