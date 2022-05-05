# -*- coding: utf-8 -*-

{
    'name': 'Production Cost',
    'version': '1.0',
    'category': 'Production',
    'sequence': 1,
    'summary': 'Calculate production cost into sale order line',
    'description': """Calculate production cost into sale order line""",
    'depends': ['sale_mrp', 'sale_management', 'sale', 'sale_approval_route'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/product_entry_data.xml',
        'views/opex_format.xml',
        'views/sale_order_view.xml',
        'views/product_entry_view.xml',
        'views/sale_report_templates.xml',
        'views/sale_report.xml',
        'views/opex_format_sale.xml'
    ],
    'demo':[],
    'installable': True,
    'application': True,
}
