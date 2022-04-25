# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, frozendict


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Register Payment'

    sale_order_id = fields.Many2one('sale.order', "Sale Order", copy=False)
    payment_term_line_ids = fields.Many2many('account.payment.term.line', 'pricelist_payment1_rel', 'pricelist_id', 'payment_id',"Milestone", copy=False)
    purchase_order_id = fields.Many2one('purchase.order', "Purchase Order", copy=False)
    po_payment_term_line_ids = fields.Many2many('account.payment.term.line', 'pricelist_payment_purchase1_rel', 'pricelist_id', 'payment_id',"Milestone", copy=False)
    
    
    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        res ={}
        pricelist_lines = []
        if self.sale_order_id:
            if self.sale_order_id.payment_detail_ids:
                for line in self.sale_order_id.payment_detail_ids:
                    pricelist_lines.append(line.payment_term_line_id.id)
            res['domain'] = {'payment_term_line_ids': [('id','in',pricelist_lines)]}
        return res
    
    @api.onchange('purchase_order_id')
    def onchange_purchase_order_id(self):
        res ={}
        pricelist_lines = []
        if self.purchase_order_id:
            if self.purchase_order_id.payment_detail_ids:
                for line in self.purchase_order_id.payment_detail_ids:
                    if not line.payment_ids:
                        pricelist_lines.append(line.payment_term_line_id.id)
            res['domain'] = {'po_payment_term_line_ids': [('id','in',pricelist_lines)]}
        return res