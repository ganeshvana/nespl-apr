from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta
from collections import defaultdict


class PurchaseTracking(models.Model):
    _name = 'purchase.tracking'
    _description = 'Purchase Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'bl_no'
    
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], "State")
    name = fields.Char("Ref")    
    purchase_id = fields.Many2one('purchase.order', "Purchase Order")    
    bl_date = fields.Date("BL Date")
    bl_qty = fields.Float("BL Qty")
    bl_no = fields.Char("BL No.")
    awb_tracking = fields.Char("AWB Tracking No.")
    bank_account_id = fields.Many2one('res.partner.bank', string="Bank")
    bank_ref_no = fields.Char("Bank Reference No.")
    eta = fields.Date("ETA")
    actual_eta = fields.Date("Actual ETA")
    free_days = fields.Integer("Free Days")
    free_days_end = fields.Date("Free Days Ends on")
    no_of_container = fields.Integer("No. of Containers")
    cha = fields.Many2one('res.partner', "CHA")
    cfs = fields.Many2one('res.partner', "CFS")
    payment_proposed_date = fields.Date("Payment Proposed Date")
    payment_clearance_date = fields.Date("Payment Clearance Date")
    import_stage_id = fields.Many2one('import.stage', string="Import Stages")
    linear_id = fields.Many2one('linear', "Liner Name")
    type = fields.Selection(related='purchase_id.type', store=True)
    tracking_container_ids = fields.One2many('tracking.containers','tracking_id', "Container")
    tracking_truck_ids = fields.One2many('tracking.truck','tracking_id', "Trucks")
    product_ids = fields.Many2many('product.product', 'product_tracking_rel', 'product_id', 'tracking_id', "Products")
    seq = fields.Integer(related='import_stage_id.sequence', store=True)
    commercial_invoice = fields.Char("Commercial Invoice")
    voyage = fields.Boolean("Voyage")
    partner_id = fields.Many2one('res.partner', "Vendor")
    
    @api.onchange('free_days', 'actual_eta')
    def onchange_actual_eta(self):
        if self.actual_eta and self.free_days:
            self.free_days_end = self.actual_eta + timedelta(days=self.free_days)
            
    @api.onchange('import_stage_id')
    def onchange_import_stage_id(self):
        if self.import_stage_id:
            if self.import_stage_id.name == 'Voyage':
                self.voyage = True
    @api.model
    def create(self, vals):
        res = super(PurchaseTracking, self).create(vals)
        sequence = self.env['ir.sequence'].next_by_code('po.tracking.seq')
        sequence = res.purchase_id.name + '/' + sequence
        res.name = sequence
        return res
    
    @api.onchange('purchase_id')
    def onchange_purchase_id(self):
        products = []
        if self.purchase_id:
            self.partner_id = self.purchase_id.partner_id
            if self.purchase_id.order_line:
                for line in self.purchase_id.order_line:
                    if line.product_id:
                        if line.product_id.id not in products:
                            products.append(line.product_id.id)
        self.product_ids = [(6,0, products)]

class PurchaseTrackingContainer(models.Model):
    _name = 'tracking.containers'
    _description = 'Tracking Container'
    
    name = fields.Char("Container")
    product_id = fields.Many2one('product.product', "Product")
    product_ids = fields.Many2many(related='tracking_id.product_ids')
    qty = fields.Float("Qty")
    vendor_id = fields.Many2one('res.partner', "Vendor")
    tracking_id = fields.Many2one('purchase.tracking', "Tracking")
    purchase_id = fields.Many2one(related='tracking_id.purchase_id')
    
    
class PurchaseTrackingTrucks(models.Model):
    _name = 'tracking.truck'
    _description = 'Tracking Trucks'
    
    container_id = fields.Many2one('tracking.containers', "Container")
    product_id = fields.Many2one(related='container_id.product_id')
    name = fields.Char("Truck")
    qty = fields.Float("Qty")
    tracking_id = fields.Many2one('purchase.tracking', "Tracking")   
    purchase_id = fields.Many2one(related='tracking_id.purchase_id')
    
