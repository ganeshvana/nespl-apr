# -*- encoding: utf-8 -*-
{
    "name": "Sale Order - Payment Link",
    "summary": "Sale Order - Payment Link",
    "license": "OPL-1",
    "depends": ["base", "sale", "stock","account"],
    "author": "Oodu Implementers Private Limited",
    "website": "https://www.odooimplementers.com",
    "category": "Accounting",
    "description": "Sale Order - Payment Link",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizard/account_payment_register_views.xml",
        "views/payment.xml",
        "views/sale.xml",
        
    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
