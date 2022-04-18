# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    tcs_account_id = fields.Many2one(
        'account.account',
        string="TCS Charge Account",
    )