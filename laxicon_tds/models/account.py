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


class AccountMove(models.Model):
    _inherit = 'account.move'

    tds_active = fields.Boolean(compute='get_tds_active')
    tds_value = fields.Monetary(string='TDS amount', compute="_compute_amount")
    tds_per = fields.Float(track_visibility='always', compute="_compute_tds_per")
    force_tds = fields.Boolean(states={'draft': [('readonly', False)]})

    valid_tds = fields.Boolean(string="TDS Applicable ?")
    tds_id = fields.Many2one('account.tds.tds', string="TDS section", states={'draft': [('readonly', False)]})
    tds_type = fields.Selection([('huf', 'Ind/Huf'), ('other', 'Other')], string="TDS type", states={'draft': [('readonly', False)]})
    nature = fields.Char(related='tds_id.nature')
    threshold_amt = fields.Float(related='tds_id.threshold_amt')
    tax_w_wo = fields.Selection(related='tds_id.tax_w_wo')
    tra_type = fields.Selection(related='tds_id.tra_type')
    ind_huf_tds_per = fields.Float(related='tds_id.ind_huf_tds_per', string="TDS %")
    other_tds_per = fields.Float(related='tds_id.other_tds_per', string="Other TDS %")
    tds_account_id = fields.Many2one(related="tds_id.account_id", string='TDS Account')
    pan = fields.Char(string='PAN Number', states={'draft': [('readonly', False)]})

    tcs_active = fields.Boolean(compute='get_tcs_active')
    tcs_value = fields.Float(compute='_compute_amount', string='TCS amount')
    tcs_per = fields.Float(track_visibility='always', compute='_compute_tcs_per')
    force_tcs = fields.Boolean(states={'draft': [('readonly', False)]})

    valid_tcs = fields.Boolean(string="TCS Applicable ?")
    tcs_id = fields.Many2one('account.tcs.tcs', string="TCS section", states={'draft': [('readonly', False)]})
    tcs_type = fields.Selection([('huf', 'Ind/Huf'), ('other', 'Other')], string="TCS type", states={'draft': [('readonly', False)]})
    tcs_nature = fields.Char(related='tcs_id.nature')
    tcs_threshold_amt = fields.Float(related='tcs_id.threshold_amt')
    tcs_tax_w_wo = fields.Selection(related='tcs_id.tax_w_wo')
    tcs_tra_type = fields.Selection(related='tcs_id.tra_type')
    ind_huf_tcs_per = fields.Float(related='tcs_id.ind_huf_tcs_per', string="TCS %")
    other_tcs_per = fields.Float(related='tcs_id.other_tcs_per', string="Other TCS %")
    tcs_account_id = fields.Many2one(related="tcs_id.account_id", string='TCS Account')

    def get_tcs_active(self):
        for i in self:
            i.tcs_active = self.env.user.company_id.tcs

    def get_tds_active(self):
        for i in self:
            i.tds_active = self.env.user.company_id.tds_active

    @api.onchange('partner_id')
    def onchnage_partner_id_tds(self):
        if self.partner_id and self.partner_id.valid_tds and self.partner_id.tds_id:
            self.clear_tds_data()
            self.valid_tds = self.partner_id.valid_tds
            self.tds_id = self.partner_id.tds_id.id
            self.tds_type = self.partner_id.tds_type
            self.nature = self.partner_id.tds_id.nature
            self.threshold_amt = self.partner_id.tds_id.threshold_amt
            self.tax_w_wo = self.partner_id.tds_id.tax_w_wo
            self.tra_type = self.partner_id.tds_id.tra_type
            self.ind_huf_tds_per = self.partner_id.tds_id.ind_huf_tds_per
            self.other_tds_per = self.partner_id.tds_id.other_tds_per
            self.tds_account_id = self.tds_id.account_id.id
            self.pan = self.partner_id.pan
        if self.partner_id and self.partner_id.valid_tcs and self.partner_id.tcs_id:
            self.clear_tcs_data()
            self.valid_tcs = self.partner_id.valid_tcs
            self.tcs_id = self.partner_id.tcs_id.id
            self.tcs_type = self.partner_id.tcs_type
            self.tcs_nature = self.partner_id.tcs_id.nature
            self.tcs_threshold_amt = self.partner_id.tcs_id.threshold_amt
            self.tcs_tax_w_wo = self.partner_id.tcs_id.tax_w_wo
            self.tcs_tra_type = self.partner_id.tcs_id.tra_type
            self.ind_huf_tcs_per = self.partner_id.tcs_id.ind_huf_tcs_per
            self.other_tcs_per = self.partner_id.tcs_id.other_tcs_per
            self.tcs_account_id = self.tcs_id.account_id.id
            self.pan = self.partner_id.pan
        if self.partner_id.pan:
            self.tcs_type = self.partner_id.check_pan_detail()

    def clear_tds_data(self):
        self.tds_id = False
        self.valid_tds = False
        self.tds_type = ''
        self.nature = ""
        self.threshold_amt = 0.0
        self.tax_w_wo = ''
        self.tra_type = 0.0
        self.ind_huf_tds_per = 0.0
        self.other_tds_per = 0.0
        self.tds_account_id = False
        self.pan = ''

    def clear_tcs_data(self):
        self.tcs_id = False
        self.tcs_type = ''
        self.tcs_nature = ""
        self.tcs_threshold_amt = 0.0
        self.tcs_tax_w_wo = ''
        self.tcs_tra_type = 0.0
        self.ind_huf_tcs_per = 0.0
        self.other_tcs_per = 0.0
        self.tcs_account_id = False
        self.pan = ''

    @api.depends('partner_id', 'valid_tcs', 'tcs_type', 'invoice_line_ids')
    def _compute_tcs_per(self):
        for res in self:
            res.tcs_per = 0.0
            if res.partner_id and res.partner_id.valid_tcs and res.move_type in ['in_refund', 'out_invoice']:
                domain = [('state', 'not in', ['cancel'])]
                amt = 0.0
                tax = 0.0
                f_amt = 0.0
                if res.tcs_id.tra_type == 'single':
                    amt = sum(line.price_subtotal for line in res.invoice_line_ids)
                elif res.tcs_id.tra_type == 'year':
                    domain.append(('invoice_date', '>=', res.tcs_id.f_start_date))
                    domain.append(('invoice_date', '<=', res.tcs_id.f_end_date))
                    inv_ids = self.search(domain)
                    for inv in inv_ids:
                        amt += sum(line.price_subtotal for line in inv.invoice_line_ids)
                if res.tcs_id.tax_w_wo == 'w_tax':
                    f_amt = amt + tax
                elif res.tcs_id.tax_w_wo == 'wo_tax':
                    f_amt = amt
                if res.partner_id.pan:
                    res.tcs_type = res.partner_id.check_pan_detail()
                if f_amt > res.tcs_id.threshold_amt:
                    if res.tcs_type == 'huf':
                        res.tcs_per = res.ind_huf_tcs_per or 0.0
                    elif res.tcs_type == 'other':
                        res.tcs_per = res.other_tcs_per or 0.0
                elif res.force_tcs:
                    if res.tcs_type == 'huf':
                        res.tcs_per = res.ind_huf_tcs_per or 0.0
                    elif res.tcs_type == 'other':
                        res.tcs_per = res.other_tcs_per or 0.0

    @api.model
    def default_get(self, fields):
        res = super(AccountMove, self).default_get(fields)
        pi_id = self.env.context.get('active_id')
        model = self.env.context.get('active_model')
        inv_type = self.env.context.get('type')
        if model == "sale.order" and inv_type == 'out_invoice':
            so = self.env[model].browse(pi_id)
            if so.partner_id and so.partner_id.valid_tcs and so.partner_id.tcs_id:
                data = {
                    'valid_tcs': True,
                    'tcs_id': so.partner_id.tds_id.id,
                    'tcs_type': so.partner_id.tcs_type
                }
                res.update(data)
        if model == "purchase.order" and inv_type == 'in_invoice':
            po = self.env[model].browse(pi_id)
            if po.partner_id and po.partner_id.valid_tds and po.partner_id.tds_id:
                data = {
                    'valid_tds': True,
                    'tds_id': po.partner_id.tds_id.id,
                    'tds_type': po.partner_id.tds_type
                }
                res.update(data)
        return res

    @api.depends('partner_id', 'valid_tds', 'tds_type', 'invoice_line_ids')
    def _compute_tds_per(self):
        for res in self:
            res.tds_per = 0.0
            if res.partner_id and res.partner_id.valid_tds and res.move_type in ['out_refund', 'in_invoice']:
                domain = [('state', 'not in', ['cancel'])]
                amt = 0.0
                tax = 0.0
                f_amt = 0.0
                if res.tds_id.tra_type == 'single':
                    amt = sum(line.price_subtotal for line in res.invoice_line_ids)
                elif res.tds_id.tra_type == 'year':
                    domain.append(('invoice_date', '>=', res.tds_id.f_start_date))
                    domain.append(('invoice_date', '<=', res.tds_id.f_end_date))
                    inv_ids = self.search(domain)
                    for inv in inv_ids:
                        amt += sum(line.price_subtotal for line in inv.invoice_line_ids)
                if res.tds_id.tax_w_wo == 'w_tax':
                    f_amt = amt + tax
                elif res.tds_id.tax_w_wo == 'wo_tax':
                    f_amt = amt
                if res.partner_id.pan:
                    res.tds_type = res.partner_id.check_pan_detail()
                if f_amt > res.tds_id.threshold_amt:
                    if res.tds_type == 'huf':
                        res.tds_per = res.ind_huf_tds_per or 0.0
                    elif res.tds_type == 'other':
                        res.tds_per = res.other_tds_per or 0.0
                elif res.force_tds:
                    if res.tds_type == 'huf':
                        res.tds_per = res.ind_huf_tds_per or 0.0
                    elif res.tds_type == 'other':
                        res.tds_per = res.other_tds_per or 0.0

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'tds_per')
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        for rec in self:
            rec.tds_value = 0.0
            if rec.tds_active and rec.tds_per > 0 and rec.move_type in ['out_refund', 'in_invoice']:
                if rec.tds_active and rec.tds_per > 0:
                    rec.tds_value = round((rec.amount_untaxed * rec.tds_per) / 100)
                    rec.amount_total = rec.amount_untaxed + rec.amount_tax - rec.tds_value
            if rec.tds_per and rec.move_type in ['out_refund', 'in_invoice']:
                rec.create_tds_journal_item()
            rec.tcs_value = 0.0
            if rec.tcs_active and rec.tcs_per > 0 and rec.move_type in ['in_refund', 'out_invoice']:
                if rec.tcs_active and rec.tcs_per > 0:
                    rec.tcs_value = round((rec.amount_untaxed * rec.tcs_per) / 100)
                    rec.amount_total = rec.amount_untaxed + rec.amount_tax + rec.tcs_value
            if rec.tcs_per and rec.move_type in ['in_refund', 'out_invoice']:
                rec.create_tcs_journal_item()
            sign = rec.move_type in ['in_refund', 'out_refund'] and -1 or 1
            rec.amount_residual_signed = rec.amount_total * sign
            rec.amount_total_signed = rec.amount_total * sign

    def create_tds_journal_item(self):
        for rec in self:
            already_exists = self.line_ids.filtered(
                lambda line: line.name and line.name.find('TDS') == 0)
            terms_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            other_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
            if already_exists:
                amount = rec.tds_value
                if rec.tds_account_id and (rec.move_type == "out_invoice" or rec.move_type == "out_refund") and rec.tds_per > 0:
                    if rec.move_type == "out_invoice":
                        already_exists.update({
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        })
                    else:
                        already_exists.update({
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        })
                total_balance = sum(other_lines.mapped('balance'))
                total_amount_currency = sum(other_lines.mapped('amount_currency'))
                terms_lines.update({
                    'amount_currency': -total_amount_currency,
                    'debit': total_balance < 0.0 and -total_balance or 0.0,
                    'credit': total_balance > 0.0 and total_balance or 0.0,
                })
            if not already_exists and rec.tds_per > 0:
                in_draft_mode = self != self._origin
                if not in_draft_mode:
                    rec.recreate_tds_journal_items()

    def recreate_tds_journal_items(self):
        for rec in self:
            type_list = ['out_refund', 'in_invoice']
            if rec.tds_per > 0 and rec.move_type in type_list:
                if rec.is_invoice(include_receipts=True):
                    in_draft_mode = self != self._origin
                    ji_name = "TDS"
                    ji_name = ji_name + " @" + str(self.tds_per) + "%"
                    terms_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    already_exists = self.line_ids.filtered(
                                    lambda line: line.name and line.name.find('TDS') == 0)
                    if already_exists:
                        amount = self.tds_value
                        if self.tds_account_id:
                            already_exists.update({
                                'name': ji_name,
                                'debit': amount < 0.0 and -amount or 0.0,
                                'credit': amount > 0.0 and amount or 0.0,
                            })
                    else:
                        create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                        if self.tds_account_id:
                            amount = self.tds_value
                            dict = {
                                    'move_name': self.name,
                                    'name': ji_name,
                                    'price_unit': self.tds_value,
                                    'quantity': 1,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                    'account_id': self.tds_account_id.id,
                                    'move_id': self._origin,
                                    'date': self.date,
                                    'exclude_from_invoice_tab': True,
                                    'partner_id': terms_lines.partner_id.id,
                                    'company_id': terms_lines.company_id.id,
                                    'company_currency_id': terms_lines.company_currency_id.id,
                                    }
                            if in_draft_mode:
                                self.line_ids += create_method(dict)
                                # Updation of Invoice Line Id
                                duplicate_id = self.invoice_line_ids.filtered(
                                    lambda line: line.name and line.name.find('TDS') == 0)
                                self.invoice_line_ids = self.invoice_line_ids - duplicate_id
                            else:
                                dict.update({
                                    'price_unit': 0.0,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                })
                                self.line_ids = [(0, 0, dict)]
                    if in_draft_mode:
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        total_balance = sum(other_lines.mapped('balance'))
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        terms_lines.update({
                                    'amount_currency': -total_amount_currency,
                                    'debit': total_balance < 0.0 and -total_balance or 0.0,
                                    'credit': total_balance > 0.0 and total_balance or 0.0,
                                })
                    else:
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        already_exists = self.line_ids.filtered(
                            lambda line: line.name and line.name.find('TDS') == 0)
                        total_balance = sum(other_lines.mapped('balance')) - amount
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        dict1 = {
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                        }
                        dict2 = {
                                'debit': total_balance < 0.0 and -total_balance or 0.0,
                                'credit': total_balance > 0.0 and total_balance or 0.0,
                                }
                        self.line_ids = [(1, already_exists.id, dict1), (1, terms_lines.id, dict2)]

    def create_tcs_journal_item(self):
        for rec in self:
            already_exists = self.line_ids.filtered(
                lambda line: line.name and line.name.find('TCS') == 0)
            terms_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            other_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
            if already_exists:
                amount = rec.tcs_value
                if rec.tcs_account_id and (rec.move_type == "out_invoice" or rec.move_type == "in_refund") and rec.tcs_per > 0:
                    already_exists.update({
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                    })
                total_balance = sum(other_lines.mapped('balance'))
                total_amount_currency = sum(other_lines.mapped('amount_currency'))
                terms_lines.update({
                    'amount_currency': -total_amount_currency,
                    'debit': total_balance < 0.0 and -total_balance or 0.0,
                    'credit': total_balance > 0.0 and total_balance or 0.0,
                })
            if not already_exists and rec.tcs_per > 0:
                in_draft_mode = self != self._origin
                if not in_draft_mode:
                    rec.recreate_tcs_journal_items()

    def recreate_tcs_journal_items(self):
        for rec in self:
            type_list = ['in_refund', 'out_invoice']
            if rec.tcs_per > 0 and rec.move_type in type_list:
                if rec.is_invoice(include_receipts=True):
                    in_draft_mode = self != self._origin
                    ji_name = "TCS"
                    ji_name = ji_name + " @" + str(self.tcs_per) + "%"
                    terms_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    already_exists = self.line_ids.filtered(
                                    lambda line: line.name and line.name.find('TCS') == 0)
                    if already_exists:
                        amount = self.tcs_value
                        if self.tcs_account_id:
                            already_exists.update({
                                'name': ji_name,
                                'debit': amount < 0.0 and -amount or 0.0,
                                'credit': amount > 0.0 and amount or 0.0,
                            })
                    else:
                        create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                        if self.tcs_account_id:
                            amount = self.tcs_value
                            dict = {
                                    'move_name': self.name,
                                    'name': ji_name,
                                    'price_unit': self.tcs_value,
                                    'quantity': 1,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                    'account_id': self.tcs_account_id.id,
                                    'move_id': self._origin,
                                    'date': self.date,
                                    'exclude_from_invoice_tab': True,
                                    'partner_id': terms_lines.partner_id.id,
                                    'company_id': terms_lines.company_id.id,
                                    'company_currency_id': terms_lines.company_currency_id.id,
                                    }
                            if self.move_type == "out_invoice":
                                dict.update({
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            if in_draft_mode:
                                self.line_ids += create_method(dict)
                                # Updation of Invoice Line Id
                                duplicate_id = self.invoice_line_ids.filtered(
                                    lambda line: line.name and line.name.find('TCS') == 0)
                                self.invoice_line_ids = self.invoice_line_ids - duplicate_id
                            else:
                                dict.update({
                                    'price_unit': 0.0,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                })
                                self.line_ids = [(0, 0, dict)]
                    if in_draft_mode:
                        # Update the payement account amount
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        total_balance = sum(other_lines.mapped('balance'))
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        terms_lines.update({
                                    'amount_currency': -total_amount_currency,
                                    'debit': total_balance < 0.0 and -total_balance or 0.0,
                                    'credit': total_balance > 0.0 and total_balance or 0.0,
                                })
                    else:
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        already_exists = self.line_ids.filtered(
                            lambda line: line.name and line.name.find('TCS') == 0)
                        total_balance = sum(other_lines.mapped('balance')) - amount
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        dict1 = {
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                        }
                        dict2 = {
                                'debit': total_balance < 0.0 and -total_balance or 0.0,
                                'credit': total_balance > 0.0 and total_balance or 0.0,
                                }
                        self.line_ids = [(1, already_exists.id, dict1), (1, terms_lines.id, dict2)]
