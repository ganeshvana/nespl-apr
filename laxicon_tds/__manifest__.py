# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': 'Laxicon TDS/TCS',
    'summary': """TDS/TCS""",
    'version': '15.1.1',
    'author': 'Laxicon Solution',
    'price': 69.0,
    'sequence': 1,
    'currency': 'USD',
    'category': 'Account',
    'website': 'https://www.laxicon.in',
    'support': 'info@laxicon.in',
    'description': """ This module manage value TDS/TCS on the total amount of Quotation, Purchase Order and Invoice (Sales & Purchase).
    After installing this module, on Settings -> Configuration -> Accounting a field is enabled for TDS/TCS.
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/account_tds_view.xml',
        'views/account_tcs_view.xml',
        'views/res_partner.xml',
        'views/res_config.xml',
    ],
    'images': ['static/description/module_image.png'],
    'installable': True,
    'application': True,
}
