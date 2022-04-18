# -*- coding: utf-8 -*-

from odoo.tools import float_round
from odoo.exceptions import ValidationError

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero
from datetime import datetime, time
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby
import json

from markupsafe import escape, Markup
from pytz import timezone, UTC
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang

class SaleOrder(models.Model):
    _inherit = 'purchase.order'

   
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
        compute='_amount_all',
        
    )
    
    @api.depends('order_line.price_total','is_tcs_apply')
    def _amount_all(self):
        for order in self:
            if order.is_tcs_apply == False:
                amount_untaxed = amount_tax = 0.0
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                order.update({
                    'amount_untaxed': order.currency_id.round(amount_untaxed),
                    'amount_tax': order.currency_id.round(amount_tax),
                    'amount_total': amount_untaxed + amount_tax,
                })
            if order.is_tcs_apply == True:
                tcs_obj = self.env['purchase.tcs.master'].search([('name','=','TCS')], limit=1)

                amount_untaxed = amount_tax = total_amount = tcs_amount = 0.0
                for line in order.order_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                    amount_total = amount_untaxed + amount_tax
                    tcs_amount = (amount_total * tcs_obj.tcs) / 100.0
                    total_amount = amount_total + tcs_amount
                order.update({
                    'amount_untaxed': order.currency_id.round(amount_untaxed),
                    'amount_tax': order.currency_id.round(amount_tax),
                    'amount_total': total_amount,
                    'tcs_value' : tcs_amount
                })
                
    

class purchase_tcs_master(models.Model):
    _name = 'purchase.tcs.master'

    name = fields.Char('Name')
    code = fields.Char('Code')
    tcs = fields.Float('TCS(in percent)',digits=dp.get_precision('Product Unit of Measure'))


