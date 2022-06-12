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


from odoo.exceptions import ValidationError
from odoo import fields, models, api
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountTCS(models.Model):
    _name = 'account.tcs.tcs'
    _description = "Account TCS Setup"

    @api.depends('tra_type', 'tax_w_wo', 'company_id')
    def compute_date(self):
        for res in self:
            today = datetime.today()
            res.curr_month = str(today.month)
            if today.month in [4, 5, 6]:
                res.curr_qtr = 'q1'
                fq_s_date = datetime(today.year, 4, 1)
                fq_e_date = datetime(today.year, 6, 30)
            elif today.month in [7, 8, 9]:
                res.curr_qtr = 'q2'
                fq_s_date = datetime(today.year, 7, 1)
                fq_e_date = datetime(today.year, 9, 30)
            elif today.month in [10, 11, 12]:
                res.curr_qtr = 'q3'
                fq_s_date = datetime(today.year, 10, 1)
                fq_e_date = datetime(today.year, 12, 31)
            elif today.month in [1, 2, 3]:
                res.curr_qtr = 'q4'
                fq_s_date = datetime(today.year, 1, 1)
                fq_e_date = datetime(today.year, 3, 31)
            if today.month in [1, 2, 3]:
                f_s_date = datetime(today.year - 1, 4, 1)
                f_e_date = datetime(today.year, 3, 31)
                year = str(today.year - 1) + "-" + str(today.year)
            else:
                f_s_date = datetime(today.year, 4, 1)
                f_e_date = datetime(today.year + 1, 3, 31)
                year = str(today.year) + "-" + str(today.year + 1)
            res.curr_year = year
            res.f_start_date = f_s_date.date()
            res.f_end_date = f_e_date.date()
            res.fq_start_date = fq_s_date.date()
            res.fq_end_date = fq_e_date.date()

    name = fields.Char(string="Section", copy=False)
    nature = fields.Char(string="Payment Nature")
    threshold_amt = fields.Float(string="Threshold Amount")
    tax_w_wo = fields.Selection([('w_tax', 'With Tax'), ('wo_tax', 'Without Tax')], string="Amount Type", default="wo_tax")
    tra_type = fields.Selection([('single', 'Single'), ('year', 'Yearly')], string="Transaction Type")

    #  for TCS
    ind_huf_tcs_per = fields.Float(string="TCS %")
    other_tcs_per = fields.Float(string="Other TCS %")
    account_id = fields.Many2one('account.account', string='Account')

    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env['res.company']._company_default_get())
    curr_year = fields.Char(string="Financial Year", compute='compute_date')
    fq_start_date = fields.Date(string="Quarter Start date", compute='compute_date')
    fq_end_date = fields.Date(string="Quarter End date", compute='compute_date')
    f_start_date = fields.Date(string="Financial Start date", compute='compute_date')
    f_end_date = fields.Date(string="Financial End date", compute='compute_date')
    curr_qtr = fields.Selection([('q1', 'Q1'), ('q2', 'Q2'), ('q3', 'Q3'), ('q4', 'Q4')], string="Current Quarter", compute='compute_date')
    curr_month = fields.Selection([('1', 'January'), ('2', 'Februay'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'June'), ('7', 'July'),
                                   ('8', 'August'), ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')],
                                  string="Current Month", compute='compute_date')

    @api.constrains('other_tcs_per', 'ind_huf_tcs_per')
    def _check_tcs_per(self):
        if self.ind_huf_tcs_per and self.ind_huf_tcs_per > 100 or self.ind_huf_tcs_per < 0:
            raise ValidationError('You cannot enter Ind/Huf TCS percentage value greater than 100.')
        if self.other_tcs_per and self.other_tcs_per > 100 or self.other_tcs_per < 0:
            raise ValidationError('You cannot enter Other TCS percentage value greater than 100.')

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.nature:
                name = name + ' (' + record.nature + ')'
            res.append((record.id, name))
        return res

    def get_date_time(self):
        for res in self:
            today = datetime.today()
            res.curr_month = str(today.month)
            if today.month in [4, 5, 6]:
                res.curr_qtr = 'q1'
                fq_s_date = datetime(today.year, 4, 1)
                fq_e_date = datetime(today.year, 6, 30)
            elif today.month in [7, 8, 9]:
                res.curr_qtr = 'q2'
                fq_s_date = datetime(today.year, 7, 1)
                fq_e_date = datetime(today.year, 9, 30)
            elif today.month in [10, 11, 12]:
                res.curr_qtr = 'q3'
                fq_s_date = datetime(today.year, 10, 1)
                fq_e_date = datetime(today.year, 12, 31)
            elif today.month in [1, 2, 3]:
                res.curr_qtr = 'q4'
                fq_s_date = datetime(today.year, 1, 1)
                fq_e_date = datetime(today.year, 3, 31)
            if today.month in [1, 2, 3]:
                f_s_date = datetime(today.year - 1, 4, 1)
                f_e_date = datetime(today.year, 3, 31)
                year = str(today.year - 1) + "-" + str(today.year)
            else:
                f_s_date = datetime(today.year, 4, 1)
                f_e_date = datetime(today.year + 1, 3, 31)
                year = str(today.year) + "-" + str(today.year + 1)
            res.curr_year = year
            res.f_start_date = datetime.strptime(f_s_date.strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
            res.f_end_date = datetime.strptime(f_e_date.strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
            res.fq_start_date = datetime.strptime(fq_s_date.strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
            res.fq_end_date = datetime.strptime(fq_e_date.strftime(DEFAULT_SERVER_DATE_FORMAT), DEFAULT_SERVER_DATE_FORMAT)
