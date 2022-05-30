# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd. (<http://devintellecs.com>).
#
##############################################################################
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class customer_wirkflow(models.Model):
    """ Add Customer Workflow """
    _inherit = 'res.partner'
    _description = 'Add workflow'

    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Validate'), ('approve', 'Approved'), ],
        string='Status', default='draft')
    sequence = fields.Char('Sequence', readonly=True, default="RP/", tracking=True, track_visiblity='onchange')

    # @api.multi
    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    # @api.multi
    def action_approve(self):
        self.write({'state': 'approve'})
        return True

    # @api.multi
    def action_validate(self):
        self.sequence = self.env['ir.sequence'].next_by_code(
            'res.partner') or 'RP/'
        self.write({'state': 'done'})
        if self.state_id.code != '08':
            fp = self.env['account.fiscal.position'].search([('name', '=', 'Inter State')], limit=1)
            if fp:
                self.property_account_position_id = fp.id
        if self.state_id.code == '08':
            self.property_account_position_id = False
        return True
