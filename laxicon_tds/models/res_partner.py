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


from odoo import fields, models, api
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    com_tds_active = fields.Boolean(compute='get_tds_active')
    valid_tds = fields.Boolean(string="TDS Applicable ?")
    tds_id = fields.Many2one('account.tds.tds', string="TDS section")
    tds_type = fields.Selection([('huf', 'Ind/Huf'), ('other', 'Other')], string="TDS type", default="other")
    nature = fields.Char(related='tds_id.nature')
    threshold_amt = fields.Float(related='tds_id.threshold_amt')
    tax_w_wo = fields.Selection(related='tds_id.tax_w_wo')
    tra_type = fields.Selection(related='tds_id.tra_type')
    ind_huf_tds_per = fields.Float(related='tds_id.ind_huf_tds_per', string="TDS %")
    other_tds_per = fields.Float(related='tds_id.other_tds_per', string="Other TDS %")
    curr_year = fields.Char(related='tds_id.curr_year')
    curr_qtr = fields.Selection(related='tds_id.curr_qtr')
    curr_month = fields.Selection(related='tds_id.curr_month')
    tds_account_id = fields.Many2one(related="tds_id.account_id", string='TDS Account')
    pan = fields.Char(string='PAN Number')
    pan_type = fields.Selection([('c', 'Company'), ('p', 'Person'), ('h', 'HUF (Hindu Undivided Family)'),
                                 ('f', 'Firm'), ('a', 'Association of Persons (AOP)'), ('t', 'AOP (Trust)'),
                                 ('b', 'Body of Individuals (BOI)'), ('l', 'Local Authority'), ('g', 'Government')])

    com_tcs_active = fields.Boolean(compute='get_tcs_active')
    valid_tcs = fields.Boolean(string="TCS Applicable ?")
    tcs_id = fields.Many2one('account.tcs.tcs', string="TCS section")
    tcs_type = fields.Selection([('huf', 'Ind/Huf'), ('other', 'Other')], string="TCS type", default="other")
    tcs_account_id = fields.Many2one(related="tcs_id.account_id", string='TCS Account')
    tcs_nature = fields.Char(related='tcs_id.nature')
    tcs_threshold_amt = fields.Float(related='tcs_id.threshold_amt')
    tcs_tax_w_wo = fields.Selection(related='tcs_id.tax_w_wo')
    tcs_tra_type = fields.Selection(related='tcs_id.tra_type')
    ind_huf_tcs_per = fields.Float(related='tcs_id.ind_huf_tcs_per', string="TCS %")
    other_tcs_per = fields.Float(related='tcs_id.other_tcs_per', string="Other TCS %")
    tcs_curr_year = fields.Char(related='tcs_id.curr_year')
    tcs_curr_qtr = fields.Selection(related='tcs_id.curr_qtr')
    tcs_curr_month = fields.Selection(related='tcs_id.curr_month')

    @api.model
    def default_get(self, fields):
        vals = super(ResPartner, self).default_get(fields)
        self.get_tds_active()
        self.get_tcs_active()
        return vals

    def get_tds_active(self):
        for i in self:
            i.com_tds_active = self.env.user.company_id.tds_active

    def get_tcs_active(self):
        for i in self:
            i.com_tcs_active = self.env.user.company_id.tcs

    @api.onchange('pan')
    def onchnage_pan_number(self):
        self.pan_type = ''
        if self.pan:
            self.pan = self.pan.upper()
            if len(self.pan) != 10:
                return {
                    'warning': {'title': 'Warning', 'message': 'Invalid PAN Number. PAN number must be 10 digits. Please check.'},
                }
            if not(re.match("[A-Z]{5}\d{4}[A-Z]{1}", self.pan.upper())):
                return {
                    'warning': {'title': 'Warning', 'message': 'Invalid PAN format.\r\n.PAN number must be in the format XXXXX0000X where 0=number, X=alphabet.'},
                }
            self.check_pan_detail()

    @api.onchange('tds_id')
    def onchnage_tds_id(self):
        if self.pan and self.tds_id:
            self.tds_type = self.check_pan_detail()

    def check_pan_detail(self):
        f_char = self.pan[3:4]
        f_l_char = f_char.lower()
        self.pan_type = f_l_char
        if f_char in ['H', 'P']:
            return 'huf'
        else:
            return 'other'
