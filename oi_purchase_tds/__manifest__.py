# -*- coding: utf-8 -*-

{
    'name': 'Purchase TDS',
    'category': 'purchase',
    'summary': 'Applies TDS tax in purchase if TDS is enabled in partner for bill above 50L',
    'version': '15.0.1.0',
    'author': 'Oodu Implementers Pvt. Ltd',
    'description': """""",
    'depends': [ 'base','purchase','account'],
    'application': True,
    'data': [
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'views/tds_view.xml'
    ],
}
