# -*- coding: utf-8 -*-
# Part of Kiran Infosoft. See LICENSE file for full copyright and licensing details.
from odoo.tools import float_round
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

class AccountInvoice(models.Model):
    _inherit = 'account.move'

   
    is_tcs_apply = fields.Boolean(
        string="Is TCS Applicable?",
        default=False,
        readonly=True,
        states={
            'draft': [('readonly', False)],
            'sent': [('readonly', False)]
        }
    )
    tcs_value = fields.Float(
        string='TCS Value',
        store=True,
        readonly=True,
        compute='_compute_tcs_value',
        
    )
   


    @api.depends(
        'invoice_line_ids.price_subtotal',        
        'currency_id',
        'company_id',
        'invoice_date',
        'move_type',
        'is_tcs_apply'
    )
    def _compute_tcs_value(self):
        res = super(AccountInvoice, self)._compute_amount()
        # changes  by me start
        for rec in self:
            if rec.move_type not in ['in_invoice','out_invoice', 'out_refund']:
                return res
            if not rec.is_tcs_apply and rec.move_type in ['out_refund']:
                return res
            # round_curr = rec.currency_id.round
            amount_total = 0.0
            for line in rec.invoice_line_ids:
                if line.name != 'TCS Charges':
                    amount_total += line.price_total
#             amount_total = rec.amount_untaxed + rec.amount_tax
            # stop
            # rounding = 0.5
            tcs_amount = 0
#             if rec.is_tcs_apply == False:
#                 amount_total = amount_total
            if rec.is_tcs_apply == True:
                tcs_obj = rec.env['purchase.tcs.master'].sudo().search([('name','=','TCS')], limit=1)
                tcs_amount = (amount_total * tcs_obj.tcs) / 100.0
                amount_total = amount_total
#             rec.amount_total = amount_total
            rec.tcs_value = tcs_amount
#     
#             amount_total_company_signed = rec.amount_total
#             amount_untaxed_signed = rec.amount_untaxed
#             if rec.currency_id and rec.company_id and rec.currency_id != rec.company_id.currency_id:
#                 currency_id = rec.currency_id
#                 amount_total_company_signed = currency_id._convert(
#                     rec.amount_total,
#                     rec.company_id.currency_id,
#                     rec.company_id,
#                     rec.invoice_date or fields.Date.today()
#                 )
#                 amount_untaxed_signed = currency_id._convert(
#                     rec.amount_untaxed,
#                     rec.company_id.currency_id,
#                     rec.company_id,
#                     rec.invoice_date or fields.Date.today()
#                 )
#             sign = rec.move_type in ['in_refund', 'out_refund'] and -1 or 1
# #             rec.amount_total_company_signed = amount_total_company_signed * sign
#             rec.amount_total_signed = rec.amount_total * sign
#             rec.amount_untaxed_signed = amount_untaxed_signed * sign

    @api.onchange('is_tcs_apply')
    def onchange_is_tcs_apply(self):
        if self.is_tcs_apply == True:
            if not self.company_id.tcs_account_id:
                raise UserError(_("Select TCS Charge Account in the Company"))
            if self.move_type == 'in_invoice':
                self.invoice_line_ids = [(0, 0,{
                    'name': 'TCS Charges',
                    'account_id': self.company_id.tcs_account_id.id,
                    'price_unit': self.tcs_value,
                    'quantity': 1,
                    'price_subtotal': self.tcs_value,
                    'debit': self.tcs_value,
    #                 'move_type': 'in_invoice',
    #                 'move_id': self._origin.id
                    })]
                if self.line_ids:
                    cred_line = self.line_ids.filtered(lambda l: l.exclude_from_invoice_tab == True and l.credit > 0)
                    if cred_line:
                        cred_line.credit +=  self.tcs_value
                        
            if self.move_type == 'out_invoice':
                self.invoice_line_ids = [(0, 0,{
                    'name': 'TCS Charges',
                    'account_id': self.company_id.tcs_account_id.id,
                    'price_unit': self.tcs_value,
                    'quantity': 1,
                    'price_subtotal': self.tcs_value,
                    'credit': self.tcs_value,
    #                 'move_type': 'in_invoice',
    #                 'move_id': self._origin.id
                    })]
                if self.line_ids:
                    cred_line = self.line_ids.filtered(lambda l: l.exclude_from_invoice_tab == True and l.debit > 0)
                    if cred_line:
                        cred_line.debit +=  self.tcs_value
        
