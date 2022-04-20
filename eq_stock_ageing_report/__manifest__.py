# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

{
    'name': "Stock Ageing Report",
    'category': 'Inventory',
    'version': '15',
    'author': 'Equick ERP',
    'description': """
        This Module allows you to generate Stock Ageing Report PDF/XLS wise.
        * Allows you to Generate Stock Ageing PDF/XLS Report.
        * Support Multi Warehouse And Multi Locations.
        * Group By Product Category Wise.
        * Filter By Product/Category Wise.
    """,
    'summary': """This Module allows you to generate Stock Ageing Report. inventory ageing report | aging report | stock aging report | inventory aging report | stock expiry report | inventory expiry report | stock aging report | inventory aging report""",
    'depends': ['base', 'stock'],
    'price': 30,
    'currency': 'EUR',
    'license': 'OPL-1',
    'website': "",
    'data': [
        'security/ir.model.access.csv',
        'report/report.xml',
        'report/stock_ageing_report.xml',
        'wizard/wizard_stock_ageing_report_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
