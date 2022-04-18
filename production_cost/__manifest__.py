# -*- coding: utf-8 -*-

{
    'name': 'Production Cost',
    'version': '1.0',
    'category': 'Production',
    'sequence': 1,
    'summary': 'Calculate production cost into sale order line',
    'description': """Calculate production cost into sale order line""",
    'depends': ['sale_mrp', 'sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_entry_data.xml',
        'views/sale_order_view.xml',
        'views/product_entry_view.xml',
    ],
    'demo':[],
    'installable': True,
    'application': True,
}
