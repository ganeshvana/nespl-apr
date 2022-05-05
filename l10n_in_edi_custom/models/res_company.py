# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_in_edi_username = fields.Char("Username")
    l10n_in_edi_password = fields.Char("Password", groups="base.group_system")
    # dummy fields
    l10n_in_edi_token = fields.Char("E-invoice (IN) Token", groups="base.group_system")
    l10n_in_edi_token_validity = fields.Datetime("E-invoice (IN) Valid Until", groups="base.group_system")
    l10n_in_edi_production_env = fields.Boolean(
        string="E-invoice (IN) Is production OSE environment",
        help="Enable the use of production credentials",
        groups="base.group_system",
    )