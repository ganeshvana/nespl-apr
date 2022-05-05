# -*- coding: utf-8 -*-

{
    'name': 'REPORT Form',
    'category': 'REPORT',
    'summary': 'Basic REPORT form',
    'version': '15.0',
    'author': 'oodu implementers ',
    'description': """""",
    'depends': ['base', 'stock','sale', 'product', 'oi_payment'],
    'application': True,
    'data': [
        'views/report.xml',
        'views/report_templates.xml',
        'views/report_taxinvoice.xml',
        'views/report_invoice.xml',
        'views/report_template_proforma.xml',
        'views/report_proforma.xml',
         'views/report_template_billmaterial.xml',
        'views/report_material.xml',
        'views/report_template_capex_bom_sale.xml',
        # 'views/manufacturing_inherit_view.xml',
        'views/sale_inherit_view.xml',
        'views/report_template_pricelist.xml',
        'views/report_pricelist.xml',
        'views/report_templates_purchase.xml',
        'views/report_purchase.xml',
        
        
        
        
       


    ],
}
