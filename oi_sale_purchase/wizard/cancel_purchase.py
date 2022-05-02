# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime,timedelta
import pdb

class PurchaseCancelReason(models.Model):
    _name='cancel.reason.purchase'
    _description="Purchase Cancel Reason"
    
    name = fields.Text('Cancel Reason')
    
class PurchaseCancel(models.Model):
    _name='cancel.purchase'
    _description="Purchase Cancel"
    
    cancel_reason_id = fields.Many2one('cancel.reason.purchase','Cancel Reason')
    purchase_id = fields.Many2one('purchase.order', "purchase")
    
    def cancel_purchase(self):
        if self.purchase_id:
            self.purchase_id.cancel_reason_id = self.cancel_reason_id.id
            self.purchase_id.button_cancel()
            
class PurchaseCreate(models.Model):
    _name='create.purchase'
    _description="Purchase Create"
    
    partner_id = fields.Many2one('res.partner','Vendor')
    product_id = fields.Many2one('product.product', "Product")
    
    def create_purchase_order(self):
        active_ids = self.env.context.get('active_ids', [])
        vendors = self.env['res.partner'].search([('id', 'in', active_ids)])
        po_list = []
        for vendor in vendors:
            vals = {'partner_id': vendor.id,
            'user_id': False,
            'company_id': self.env.company.id,
            'currency_id': vendor.with_company(self.env.company).property_purchase_currency_id.id or self.env.company.currency_id.id,
            'payment_term_id': vendor.with_company(self.env.company).property_supplier_payment_term_id.id,
            'date_order': fields.Date.today(),
            }
            po = self.env['purchase.order'].create(vals)
            po_list.append(po.id)
            purchase_line = self.env['purchase.order.line'].create({
                'product_id': self.product_id.id,
                'name':self.product_id.name,
                'order_id': po.id
                })
            
        action = self.env.ref("purchase.purchase_rfq")
        result = action.read()[0]
        result["domain"] = [("id", "in", po_list)]
        return result
        