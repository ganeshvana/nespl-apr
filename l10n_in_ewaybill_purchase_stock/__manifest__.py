# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "eWayBill for India (Purchase-Stock)",
    "summary": """
        Create an eWayBill to transer the goods in India""",
    "description": """
        This module link Purchase bill and stock picking to get bill and ship address
    """,
    "author": "Odoo",
    "website": "http://www.odoo.com",
    "category": "Accounting/Accounting",
    "version": "1.0",
    "depends": ["purchase", "l10n_in_ewaybill", "l10n_in_ewaybill_stock"],
    "installable": True,
    "auto_install": True,
    "license": "OEEL-1",
}
