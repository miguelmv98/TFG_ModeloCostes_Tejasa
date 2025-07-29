{
    'name': 'Modelo Costes',
    'version': '1.0',
    'summary': 'Calcula el coste total para los pedidos completados',
    'author': 'Miguel Monje',
    #'website': 'https://www.odoo.com/page/modelo_costes',
    #'license': 'License',
    "depends": [
        "base"
    ],
    'data': [
        'views/time_record_view.xml',
        'views/import_time_record_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    "application": True
}
