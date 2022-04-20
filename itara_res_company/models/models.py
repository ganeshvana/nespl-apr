# -*- coding: utf-8 -*-

from odoo import models, fields, api

class rescompany(models.Model):
    _inherit = 'res.company'
  
    # loc_com_name = fields.Char(string='Company Location Name')
    bank_name = fields.Char(string='Bank Name')
    bank_branch = fields.Char(string='Bank Branch')    
    ac_no = fields.Char(string='A/C No')
    ifsc_code = fields.Char(string='IFSC Code')
    swift_code = fields.Char(string='Swift Code')
    gst_no = fields.Char(string='GSTIN')
    # state_name_code = fields.Char(string='State Name & Code')
    pan_no = fields.Char(string='PAN No')