# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nimisha Muralidhar (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import base64
import io

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
# from datetimerange import DateTimeRange
from datetime import timedelta
import sys

          
class IndentComparision(models.TransientModel):
    _name = 'indent.comparision.report'
    
    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()
    purchase_indent = fields.Many2one('purchase.requisition', "Indent", tracking=True)
    
    def generate_report(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Indent Comparision')
        style_highlight_right = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'right'})
        style_highlight = workbook.add_format({'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
        style_normal = workbook.add_format({'align': 'left'})
        style_right = workbook.add_format({'align': 'right'})
        style_left = workbook.add_format({'align': 'left'})
        merge_formatb = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'bg_color': '#FFFFFF',
                'text_wrap': True
                })
        merge_formatb.set_font_size(9)
        headers = []
        row = 1
        col = 0
        for line in self.purchase_indent.purchase_ids:
            if line.partner_id not in headers:
                headers.append(line.partner_id)
        vendor_dict = {}        
        for i in headers:
            vendor_dict[i] = 0.0
        mrg = 'A' + str(row) + ':G' + str(row)
        worksheet.merge_range(mrg, 'Indent ' + self.purchase_indent.name, merge_formatb)
        worksheet.set_column(col, col, 40)
        row += 1
        col = 1
        fcol = 1 
        lcol = 3
        for header in headers:   
            worksheet.set_column(col, col, 20)         
            worksheet.merge_range(row, fcol, row, lcol, header.name, merge_formatb)
            # worksheet.write(row, col, header.name, style_highlight)
            
            fcol += 3     
            lcol += 3  
        row += 1
        title = ["Payment Term", "Make", "Price","Payment Term", "Make", "Price","Payment Term", "Make", "Price" ]
        if self.purchase_indent:
            quotations = self.purchase_indent.purchase_ids     
        col = 1
        for t in title:            
            worksheet.write(row, col, t, merge_formatb)
            worksheet.set_column(col, col, 20)
            col+=1
        row += 1
        for pil in self.purchase_indent.line_ids:
            col = 0 
            worksheet.write(row, col, str(pil.product_id.name+ '['+ pil.product_id.default_code + ']'),style_normal)
            col += 1
            quote_liness = self.env['purchase.order.line'].search([('order_id', 'in', quotations.ids)])
            if quote_liness:
                quote_lines = quote_liness.filtered(lambda d: d.product_id == pil.product_id)
                if quote_lines:
                    for line in quote_lines: 
                        if line.partner_id:
                            vendor_dict[line.partner_id] = [line.order_id.payment_term_id.name, line.model.name, line.price_unit]
                    for val in vendor_dict.values():
                        if val != 0.0:
                            worksheet.write(row, col, val[0],style_left)
                            col += 1
                            worksheet.write(row, col, val[1],style_left)
                            col += 1
                            if val[2] == 0.0:
                                pr = ''
                            else:
                                pr = str("%.2f" % val[2] + line.order_id.currency_id.symbol)
                            worksheet.write(row, col, pr,style_right)                     
                            col += 1        
            row += 1
        
        workbook.close()
        xlsx_data = output.getvalue()
        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "IndentComparision.xlsx"
 
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        } 
            
       