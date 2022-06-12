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

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    tcs = fields.Boolean(string='Allow TCS', help="Allow TCS in Sale Invoice")
    tds_active = fields.Boolean(string='Allow TDS', help="Allow TDS in Purchase bill")


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tcs = fields.Boolean(related="company_id.tcs", string='Allow TCS', help="Allow TCS in Sale Invoice", readonly=False)
    tds_active = fields.Boolean(related="company_id.tds_active", string='Allow TDS', help="Allow TDS in Purchase bill", readonly=False)
