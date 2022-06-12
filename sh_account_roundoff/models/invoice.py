# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    sh_round = fields.Boolean("Rounding Line")

    @api.depends('debit', 'credit', 'amount_currency', 'account_id', 'currency_id', 'move_id.state', 'company_id',
                 'matched_debit_ids', 'matched_credit_ids')
    def _compute_amount_residual(self):
        """ Computes the residual amount of a move line from a reconcilable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconcilable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
        for line in self:
            if line.id and (line.account_id.reconcile or line.account_id.internal_type == 'liquidity'):
                reconciled_balance = sum(line.matched_credit_ids.mapped('amount')) \
                    - sum(line.matched_debit_ids.mapped('amount'))
                reconciled_amount_currency = sum(line.matched_credit_ids.mapped('debit_amount_currency'))\
                    - sum(line.matched_debit_ids.mapped('credit_amount_currency'))

                if self.company_id.sh_enable_round_off:
                    line.amount_residual = round(
                        line.balance - reconciled_balance)
                else:
                    line.amount_residual = line.balance - reconciled_balance

                if self.company_id.sh_enable_round_off:

                    if line.currency_id:
                        line.amount_residual_currency = round(
                            line.amount_currency - reconciled_amount_currency)
                    else:
                        line.amount_residual_currency = 0.0
                else:

                    if line.currency_id:
                        line.amount_residual_currency = line.amount_currency - reconciled_amount_currency
                    else:
                        line.amount_residual_currency = 0.0
                line.reconciled = line.company_currency_id.is_zero(line.amount_residual) \
                    and (not line.currency_id or line.currency_id.is_zero(line.amount_residual_currency))

            else:
                # Must not have any reconciliation since the line is not eligible for that.
                line.amount_residual = 0.0
                line.amount_residual_currency = 0.0
                line.reconciled = False


class AccountMove(models.Model):
    _inherit = 'account.move'

    sh_round_amount = fields.Monetary(
        "Round Off Amount", compute='_compute_amount', readonly=True,compute_sudo = True)
    sh_round_off_total = fields.Monetary(
        "Round Off Total", compute='_compute_amount', readonly=True,compute_sudo = True)

    @api.model
    def _get_invoice_in_payment_state(self):
        ''' Hook to give the state when the invoice becomes fully paid. This is necessary because the users working
        with only invoicing don't want to see the 'in_payment' state. Then, this method will be overridden in the
        accountant module to enable the 'in_payment' state. '''
        return 'paid'

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
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:

            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id and line in move._get_lines_onchange_currency():
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * \
                (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * \
                (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * \
                (total_currency if len(currencies) == 1 else total)
            move.amount_residual = -sign * \
                (total_residual_currency if len(currencies) == 1 else total_residual)
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(
                total) if move.move_type == 'entry' else -total
            move.amount_residual_signed = total_residual
            move.sh_round_off_total = round(move.amount_total)
            move.sh_round_amount = round(move.amount_total) - move.amount_total

            currency = len(currencies) == 1 and currencies.pop(
            ) or move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(include_receipts=True) and move.state == 'posted':

                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                reverse_moves_full_recs = reverse_moves.mapped(
                    'line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

    def _recompute_dynamic_lines(self, recompute_all_taxes=False, recompute_tax_base_amount=False):
        res = super(AccountMove, self)._recompute_dynamic_lines(
            recompute_all_taxes, recompute_tax_base_amount)

        for invoice in self:
            if invoice.company_id.sh_enable_round_off and invoice.sh_round_off_total > 0:
                if not invoice.company_id.sh_round_off_account_id:
                    raise UserError(_("Please set Round of Account !"))
                debit_line = False
                credit_line = False
                account_id = False
                if invoice.is_sale_document(include_receipts=True):
                    account_id = invoice.partner_id.property_account_receivable_id
                else:
                    account_id = invoice.partner_id.property_account_payable_id

                for line in invoice.line_ids:
                    if line.account_id == account_id:
                        if line.debit > 0:
                            line.debit = invoice.sh_round_off_total

                            if invoice.sh_round_off_total < invoice.amount_total:
                                debit_line = True
                            else:
                                credit_line = True

                        if line.credit > 0:
                            line.credit = invoice.sh_round_off_total

                            if invoice.sh_round_off_total < invoice.amount_total:
                                credit_line = True
                            else:
                                debit_line = True

                sh_round_line = invoice.line_ids.filtered(
                    lambda x: x.account_id == invoice.company_id.sh_round_off_account_id)
                invoice.line_ids -= sh_round_line
                if debit_line:
                    if invoice.sh_round_amount < 0:
                        create_method = self.env['account.move.line'].new or self.env['account.move.line'].create
                        sh_rounding_line = create_method({
                            'account_id': invoice.company_id.sh_round_off_account_id.id,
                            'debit': invoice.sh_round_amount * (-1),
                            'credit': 0.0,
                            'name': 'Round Off Amount',
                            'exclude_from_invoice_tab': True,
                            'is_rounding_line': False,
                            'sh_round': True
                        })
                        invoice.line_ids += sh_rounding_line
                    else:
                        create_method = self.env['account.move.line'].new or self.env['account.move.line'].create
                        sh_rounding_line = create_method({
                            'account_id': invoice.company_id.sh_round_off_account_id.id,
                            'debit': invoice.sh_round_amount,
                            'credit': 0.0,
                            'name': 'Round Off Amount',
                            'exclude_from_invoice_tab': True,
                            'is_rounding_line': False,
                            'sh_round': True
                        })
                        invoice.line_ids += sh_rounding_line

                if credit_line:
                    if invoice.sh_round_amount < 0:
                        create_method = self.env['account.move.line'].new or self.env['account.move.line'].create
                        sh_rounding_line = create_method({
                            'account_id': invoice.company_id.sh_round_off_account_id.id,
                            'debit': 0.0,
                            'credit': invoice.sh_round_amount * (-1),
                            'name': 'Round Off Amount',
                            'exclude_from_invoice_tab': True,
                            'is_rounding_line': False,
                            'sh_round': True
                        })

                        invoice.line_ids += sh_rounding_line
                    else:
                        create_method = self.env['account.move.line'].new or self.env['account.move.line'].create
                        sh_rounding_line = create_method({
                            'account_id': invoice.company_id.sh_round_off_account_id.id,
                            'debit': 0.0,
                            'credit': invoice.sh_round_amount,
                            'name': 'Round Off Amount',
                            'exclude_from_invoice_tab': True,
                            'is_rounding_line': False,
                            'sh_round': True
                        })
                        invoice.line_ids += sh_rounding_line
        return res
