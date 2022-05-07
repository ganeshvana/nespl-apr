# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class Helpdesk(models.Model):
    _inherit = 'helpdesk.ticket'
        
    partner_id = fields.Many2one('res.partner', "Partner")
    sale_order_id = fields.Many2one('sale.order', "Sale Order")
    sale_product_id = fields.Many2one('product.product', "Product")
    product_ids = fields.Many2many('product.product', 'product_helpdesk_rel', 'product_id', 'helpdesk_id', "Products")
    stock_production_lot_id = fields.Many2one('stock.production.lot', "Lot No.")
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    
    @api.onchange('sale_product_id')
    def onchange_sale_product_id(self):
        if self.sale_product_id:
            self.product_id = self.sale_product_id.id
    
    @api.onchange('employee_pin', 'employee_id')
    def onchange_employee_pin(self):
        if self.employee_pin and not self.employee_id:
            raise ValidationError("Select Employee")
        # if self.employee_pin and self.employee_id:
        #     if self.employee_pin != self.employee_id.employee_pin:
        #         raise ValidationError("PIN is wrong!!!")
        
    # def write(self, vals):
    #     res = super(Helpdesk, self).write(vals)
    #     for rec in self:
    #         if rec.employee_id and not rec.employee_pin:
    #             raise ValidationError("Enter Employee PIN !!!")
    #         if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
    #             raise ValidationError("PIN is wrong!!!")
    #         if 'employee_pin' in vals:
    #             if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
    #                 raise ValidationError("PIN is wrong!!!")
    #     return res
    
    @api.onchange('partner_id', 'sale_order_id', 'stock_production_lot_id')
    def onchange_partner_id(self):
        res = {}
        sale_order = []
        lots = []
        if not self.partner_id:
            sale_order = self.env['sale.order'].search([]).ids
            lots = self.env['stock.production.lot'].search([]).ids        
        if not self.sale_order_id:
            lots = self.env['stock.production.lot'].search([]).ids
        if not self.stock_production_lot_id :
            sale_order = self.env['sale.order'].search([]).ids
        if self.partner_id:
            sale_order = self.partner_id.sale_order_ids.ids
            # self.partner_category_id = [(6, 0, self.partner_id.category_id.ids)]
        if self.stock_production_lot_id:
            sale_order = self.stock_production_lot_id.sale_order_ids.ids
            if self.stock_production_lot_id.sale_order_ids:
                self.partner_id = self.stock_production_lot_id.sale_order_ids[0].partner_id.id
        if self.sale_order_id:
            self.partner_id = self.sale_order_id.partner_id.id
            lot = self.env['stock.production.lot'].search([])
            if lot:
                for l in lot:
                    if l.sale_order_ids:
                        for s in l.sale_order_ids:
                            if s.id == self.sale_order_id.id:
                                lots.append(l.id)
        
        res['domain'] = {'sale_order_id': [('id','in',sale_order)], 'stock_production_lot_id': [('id','in',lots)]}
        return res 
    
    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        if self.sale_order_id:
            products = []
            for line in self.sale_order_id.order_line:
                if line.product_id:
                    if line.product_id.id not in products:
                        products.append(line.product_id.id)
            self.product_ids = [(6,0, products)]
                
            
    
    @api.onchange('helpdesk_name_id')
    def onchange_helpdesk_name_id(self):
        if self.helpdesk_name_id:
            self.name = self.helpdesk_name_id.name
              