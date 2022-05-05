# -*- coding: utf-8 -*-
{
    'name': 'Sale Dynamic Approval Process',
    'version': '1.4.04',
    'summary': """
    Sale Approval
    """,
    'category': 'Sale',
    'author': 'XFanis',
    'support': 'odoo@xfanis.dev',
    'website': 'https://xfanis.dev',
    'license': 'OPL-1',
    'description':
        """
        Sale Approval
 
        """,
    'data': [
        'security/ir.model.access.csv',
        'security/sale_security.xml',
        'data/sale_approval_route.xml',
        'views/sale_approval_route.xml',
        # 'views/res_config_settings_views.xml',
    ],
    'depends': ['sale', 'sale_project', 'sale_management'],
    'qweb': [],
    
    'installable': True,
    'auto_install': False,
    'application': True,
}
