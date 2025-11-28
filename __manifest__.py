{
    'name': 'Modelo Costes',
    'version': '1.0',
    'summary': 'Calcula el coste total para los pedidos completados',
    'author': 'Miguel Monje',
    #'website': 'https://www.odoo.com/page/modelo_costes',
    #'license': 'License',
    'external_dependencies': {
        'python': [
            'requests',       # Python library installed with pip
            'pandas'
        ],
        'bin': [
            'wkhtmltopdf',    # System command / binary
            #'unoconv'
        ],
    },
    "depends": [
        "web",
        "base",
        "hr",
        "mrp",
        "product",
        "stock",
        "account",
        "stock_account",
        "recursive_tree_view"
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/time_record_wizard_view.xml',
        'views/time_record_views.xml',
        'views/time_record_wizard_logs_views.xml',
		'report/time_record_report_views.xml',
        'report/components_report_views.xml',
		'report/sold_products_report_views.xml',
		'report/bought_products_report_views.xml',
		'report/account_balance_report_views.xml',
        'views/account_summary_report_views.xml',
		'views/account_summary_views.xml',
		'wizard/inventory_report_wizard_view.xml',
		'views/inventory_report_view.xml',
        'wizard/cost_model_wizard_view.xml',
        'views/cost_model_views.xml',
        'views/cp_menu_views.xml',
],
     "assets": {
         "web.assets_backend": [
            "cost_product/static/account_kpis_config.json",
            "cost_product/static/src/css/full_sheet.css"
         ],
     },
    'installable': True,
    'auto_install': False,
    "application": True
}
