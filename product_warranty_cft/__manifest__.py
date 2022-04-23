# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Product Warranty',
    'version' : '1.0',
    'author':'Craftsync Technologies',
    'category': 'Sales',
    'maintainer': 'Craftsync Technologies',
    'website': 'https://www.craftsync.com/',
    'summary': "Create Warranty And track of Warranty Claim",

    'data' : [
        'security/ir.model.access.csv',  
        'view/product_category.xml',  
        'view/res_partner.xml',
        'wizard/view_warranty_wizard.xml',
        'wizard/generate_warranty_claim.xml',
        'wizard/send_mail_to_partner.xml',
        'view/sale_order.xml',
        'view/purchase_order.xml',
        'view/view_product.xml',
        'view/view_warranty_card.xml',
        'view/stock.xml',
        'view/invoice.xml',
        'view/product_warranty_config.xml', 
        'report/warranty_card_report.xml',
        'report/warranty_card_report_templates.xml',
        'view/mail_template.xml',
               
              ],
    'license': 'OPL-1',
    'support':'info@craftsync.com',
    'depends' : ['sale_management','purchase','sale_stock','account'],

    'images': ['static/description/main_screen.png'],

    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 36.99,
    'currency': 'EUR',

}
