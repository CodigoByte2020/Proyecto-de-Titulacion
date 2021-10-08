{
    'name': 'Compras',
    'summary': 'Módulo de Compras',
    'description': 'Módulo para la gestión de compras.',
    'author': 'Contreras Pumamango Gianmarco - gmcontrpuma@gmail.com',
    'website': 'https://github.com/CodigoByte2020',
    'category': 'Tools',
    'version': '13.0.0.0.1',
    'depends': [
        'inventario'
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/compras_menus_views.xml',
        'views/compras_views.xml',
        'views/proveedor_views.xml'
    ],
    'installable': True,
}
