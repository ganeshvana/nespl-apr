
{
    'name': 'Sale Order - Extended',
    'version': '1.0',
    'category': 'Generic Modules/Account',
    'summary': 'Additional changes in sale order',
    'description': """This module contains additional state added to sale order form as proforma invoice and send by mail option for proforma invoice""",
    'author': 'Oodu Implementers Pvt Ltd.',
    'website': "https://www.odooimplementers.com",
    # 'images':['static/description/testing.png',],
    'depends': ['base', 'sale', 'sales_team','sale_management','itara_res_company'],
    'data': ['data/sale_view.xml',
             'views/proforma_invoice_report.xml',
             'views/proforma_invoice_report_view.xml'
    ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'auto_install': False,
    'application': True,
  }
