
{
    'name': 'Proforma Invoice with Header',
    'version': '14.0.1.0',
    'category': 'Generic Modules/Account',
    'summary': 'Proforma Invoice with Header',
    'description': """This module contains template for proforma invoice with header""",
    'author': 'Oodu Implementers Pvt Ltd.',
    'website': "https://www.odooimplementers.com",
    'depends': ['base', 'sale', 'sale_management','itara_res_company'],
    'data': [
             
             'views/proforma_invoice_report.xml',
             'views/proforma_invoice_report_view.xml'
    ],
    'demo': [ ],
    'test': [ ],
    'installable': True,
    'auto_install': False,
    'application': True,
  }
