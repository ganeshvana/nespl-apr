# -*- coding: utf-8 -*-
{
    'name': 'Custom Sales',
    'version': '0.1',
    'category': 'Facility',
    'license': 'OPL-1',
    'author': 'Odoo implementers Pvt. Ltd.',
    'currency': 'EUR',
    'summary': 'Custom Sales',
    'description': """
    Custom Sales
""",
    'depends': ['base', 'mail', 'sale', 'purchase', 'account', 'product', 'sale_project', 'purchase_requisition', 'production_cost'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/cancel_purchase.xml',
        # 'report/letter_print.xml',
        'views/res_partner.xml',
        'views/purchase.xml',
    ],
    'installable': True,
    'application': True,
    
}
