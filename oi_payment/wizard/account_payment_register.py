# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, frozendict

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime,timedelta,timezone
from dateutil.relativedelta import relativedelta
import base64
import io
import os
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo.modules.module import get_resource_path
from odoo.tools.misc import xlsxwriter
from odoo.tools.mimetypes import guess_mimetype
import os.path
from os import path
from pathlib import Path
import collections, functools, operator
from collections import Counter
from reportlab.rl_settings import rtlSupport
from datetime import  date
from datetime import timedelta
import sys
import pytz


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

class PaymentExport(models.TransientModel):
    _name = 'payment.export'    
    _description = 'Payment Export'    
    
    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()
    name_file = fields.Char("File Name", required=True)
    
    def generate_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Payment')
        style_highlight_right = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'right'})
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'align': 'left', 'bg_color': '#FFFFFF',})
        style_normal = workbook.add_format({'align': 'center'})
        style_right = workbook.add_format({'align': 'right'})
        style_left = workbook.add_format({'align': 'left'})
        count = 0
        active_ids = self.env.context.get('active_ids')
        merge_formatb = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#FFFFFF',
                'text_wrap': True
                })
        merge_formatb.set_font_size(9)
        headers = [
            "From A/C No.",
            "A/C no.",
            "Beneficiary Name",
            "Amount",
            "Payment Mode",
            "Date",            
            "IFSC code",            
            "Payable Location",
            "Print Location",
            "Mobile No",
            "Mail ID",
            "Bene Address 1",
            "Bene Address 2",
            "Bene Address 3",
            "Bene Address 4",
            "Add Detail 1",
            "Add Detail 2",
            "Add Detail 3",
            "Add Detail 4",
            "Add Detail 5",
            "Remark"
            
        ]
        row = 0
        col = 0
        for header in headers:
            worksheet.write(row, col, header, style_highlight)
            worksheet.set_column(col, col, 16)
            col += 1       
        row += 1
        col = 0
        for payment in self.env['account.payment'].search([('id', 'in', active_ids)]):            
            col = 0 
            worksheet.write(row, col, payment.journal_id.bank_account_id.acc_number,style_left)
            col += 1    
            if payment.partner_bank_id:
                pbank = payment.partner_bank_id.acc_number
                pifsc = payment.partner_bank_id.bank_id.bic
            else:
                pbank = ''
                pifsc = ''     
            worksheet.write(row, col, pbank,style_left)
            col += 1
            worksheet.write(row, col, payment.partner_id.name,style_left)
            col += 1
            worksheet.write(row, col, payment.amount,style_right)
            col += 1
            worksheet.write(row, col, str(payment.payment_mode),style_normal)
            col += 1     
            worksheet.write(row, col, str(payment.date.strftime('%d-%b-%Y')),style_left)
            col += 1            
            worksheet.write(row, col, pifsc,style_left)
            col += 1
            row += 1
        workbook.close()
        xlsx_data = output.getvalue()
        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = self.name_file + '.xlsx'
 
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }  