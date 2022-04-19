# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

states = [('draft', 'Draft'), ('approved', 'Approved')]

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    bom_id = fields.Many2one('mrp.bom', "BoM")
    

    @api.onchange('bom_id')
    def onchange_bom_id(self):
        if self.bom_id:
            self.sale_term = self.template_id.template
            
