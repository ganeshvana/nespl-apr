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
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    quote_media = fields.Char("Media")
    project_id = fields.Many2one('project.project', "Project")
    
    
    @api.onchange('employee_pin', 'employee_id')
    def onchange_employee_pin(self):
        if self.employee_pin and not self.employee_id:
            raise ValidationError("Select Employee")
        # if self.employee_pin and self.employee_id:
        #     if self.employee_pin != self.employee_id.employee_pin:
        #         raise ValidationError("PIN is wrong!!!")
        
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        for rec in self:
            if rec.employee_id and not rec.employee_pin:
                raise ValidationError("Enter Employee PIN !!!")
            if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
                raise ValidationError("PIN is wrong!!!")
            if 'employee_pin' in vals:
                if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
                    raise ValidationError("PIN is wrong!!!")
        return res
    
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
        
class PRL(models.Model):
    _inherit = 'purchase.requisition.line'
    
    product_tmpl_id = fields.Many2one('product.template', 'Product')
    model = fields.Char("Make/Model")
    product_id = fields.Many2one('product.product', "Product", required=False)

        
class Pricelist(models.Model):
    _inherit = 'product.pricelist.item'
    
    product_uom_id = fields.Many2one(related='product_tmpl_id.uom_id')
    wp = fields.Float("Wp Price", compute='compute_wp', store=True)
    kwp = fields.Float("KWp Price", compute='compute_wp', store=True)
    kilow = fields.Float("KWp", compute='compute_wp', store=True)
    
    @api.depends('product_id.product_template_attribute_value_ids', 'product_id.product_template_attribute_value_ids.attribute_id', 'min_quantity', 'fixed_price')
    def compute_wp(self):
        for rec in self:
            watt = 0.0
            if rec.product_id.product_template_attribute_value_ids:
                for line in rec.product_id.product_template_attribute_value_ids:
                    if line.attribute_id.name == 'Wattage':
                        watt = int(line.name)
                        if watt > 0.0:
                            rec.wp = float(rec.fixed_price) / int(watt)
                            rec.kwp = float(rec.min_quantity * rec.fixed_price) / int(watt)
                            rec.kilow = (int(watt) * rec.min_quantity) / 1000
                        else:
                            rec.wp = 0.0
                            rec.kwp = 0.0
                            rec.kilow = 0.0
                    else:
                        rec.wp = 0.0
                        rec.kwp = 0.0
                        rec.kilow = 0.0
    