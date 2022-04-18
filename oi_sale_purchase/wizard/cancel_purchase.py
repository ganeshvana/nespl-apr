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