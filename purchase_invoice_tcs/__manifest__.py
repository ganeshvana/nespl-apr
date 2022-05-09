# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
{
    'name': "TCS on Purchase and Vendor Bills",
    'summary': """TCS on Purchase and Vendor Bills""",
    'description': """
- TCS amount (0.075%) should be arrived automatically from total amount calculation.
- Applies only purchase order to vendor bill.
""",
    "version": "12.0.1.0",
    "category": "Purchases",
    'author': "oodu implementers pvt ltd",
    "website": "http://www.odooimplementers.com.com",
    'license': 'Other proprietary',
    "depends": ['base','purchase','account'],
    "data": [
        'security/ir.model.access.csv',
        'views/res_company_view.xml',
        'views/purchase_order_view.xml',
        'views/account_invoice_view.xml',
    ],
    "application": False,
    'installable': True,
}
