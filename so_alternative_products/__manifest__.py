# -*- coding: utf-8 -*-
{
    'name': "Sale Order Alternative Products",

    'summary': "This Module allows user to add Alternative products in your self "
               "product and replace the product with the product alternative",
    'description': "",
    'author': "Abderrahmane ratib",
    'website': "",
    'license': 'AGPL-3',
    'category': 'Sales',
    'version': '13.0.1',
    'depends': ['base', 'sale'],
    'data': [
        'views/alternative_views.xml',
        'views/products_wizard.xml',
        'views/sales_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': ['static/description/banner.png'],
    'live_test_url': "https://youtu.be/SfNM-qmThLw",
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 99,
    'currency': 'EUR',
    
}