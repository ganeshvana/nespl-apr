# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cancel_reason_id = fields.Many2one('cancel.reason.purchase','Cancel Reason')
    
    def action_cancel(self):
        view = self.env.ref('oi_sale_purchase.cancel_purchase_view_form')
        self = self.with_context(default_purchase_id = self.id)
        
        return {
            'name': 'Purchase Cancel',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cancel.purchase',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': self._context,
        }