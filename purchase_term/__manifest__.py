# -*- coding: utf-8 -*-
{
    'name': 'Dynamic Sales Terms and Condition',
    'version': '0.1',
    'category': 'Facility',
    'license': 'OPL-1',
    'price': 40.00,
    'author': 'Odoo implementers Pvt. Ltd.',
    'currency': 'EUR',
    'summary': 'Sales Terms, Conditions, Agreements, Contracts in Quotation and Sale order',
    'description': """
    Warranty List
    Sales Warranty Cards
    Warranty Template
    Design Sales agreements
    Agreements sales
""",
    'depends': ['base', 'mail', 'sale', 'purchase', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'report/letter_print.xml',
        'views/sale_letter_pad.xml',
    ],
    'installable': True,
    'application': True,
}
