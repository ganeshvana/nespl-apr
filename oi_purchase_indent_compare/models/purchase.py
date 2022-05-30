from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta
from collections import defaultdict


class Purchase(models.Model):
    _inherit = 'purchase.order'
    
    # purchase_order_type_id = fields.Many2one('purchase.order.type', "Order Type")
    expire_date = fields.Date("Expiry Date")
    cancel_reason = fields.Text("Cancel Reason")
    transport_mode = fields.Selection([('sea','Sea'),('air','Air'),('road', 'Road'),('courier', 'Courier')], string="Mode of Transport")
    sea_port = fields.Many2one('sea.port', "Sea Port")
    air_port = fields.Many2one('air.port', "Air Port")
    port = fields.Char("Port")
    indent_date = fields.Date("Indent Ref Date")
    
    @api.onchange('date_order')
    def onchange_date_order(self):
        if self.date_order:
            self.expire_date = self.date_order.date() + timedelta(days=45)
    

    def send_approve_delay(self):
        purchase = self.env['purchase.order'].search([('state', 'in', ['purchase','done','cancel'])])
        if purchase:            
            for po in purchase:
                if po.create_date.date() +  timedelta(days=po.team_id.escalation_days) >= fields.Date.today():  
                    mail_template_id = self.env.ref('oi_purchase.mail_template_send_approve_delay')
                    self.env['mail.template'].browse(mail_template_id.id).send_mail(po.id, force_send=True) 
    
    def button_cancel(self):
        res = super(Purchase, self).button_cancel() 
        if not self.cancel_reason:
            raise UserError(_('Enter Cancel Reason.'))
        return res
    
    def button_draft(self):
        res = super(Purchase, self).button_draft() 
        if self.cancel_reason:
            self.cancel_reason = False
        return res

                
class purchaseLine(models.Model):
    _inherit = 'purchase.order.line'   
    
    agent_id = fields.Many2one('res.partner', "Agent")
    origin_id = fields.Many2one('purchase.origin',"Origin")
    picking_type_id = fields.Many2one(related='order_id.picking_type_id')
    
    @api.onchange('date_planned')
    def onchange_date_planned(self):
        if self.date_planned:
            if self.order_id.expire_date:
                if self.date_planned.date() > self.order_id.expire_date:
                    raise UserError(_('Delivery date cannot be greater than expire date.'))
                
    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self.product_qty:
            if self.product_id.orderpoint_ids:
                op = self.product_id.orderpoint_ids.filtered(lambda p: p.location_id == self.picking_type_id.default_location_dest_id)
                if op:
                    print(op, "op=======", op.product_max_qty, op.product_id.name)
                    if self.product_qty > op.product_max_qty:
                        raise UserError(_('Order Qty cannot be greater than Max Qty.'))

class ApprovalApprover(models.Model):
    _name = 'purchase.approval.approver'
    _description = 'Approver'
#
#
#     purchase_order_id = fields.Many2one('purchase.order', "Order")
#     user_id = fields.Many2one('res.users', string="User", required=True,)
#     status = fields.Selection([
#         ('new', 'New'),
#         ('pending', 'To Approve'),
#         ('approved', 'Approved'),
#         ('refused', 'Refused'),
#         ('cancel', 'Cancel')], string="Status", default="new", readonly=True)
#
#
#     required = fields.Boolean(default=False, readonly=True)
    
class Picking(models.Model):
    _inherit = 'stock.picking'

    commercial_invoice = fields.Char("Commercial Invoice")
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
    tracking_id = fields.Many2one('purchase.tracking', "Purchase Tracking")
    
    def button_validate(self):
        if self.tracking_id:
            if not self.tracking_id.import_stage_id.name == 'Cleared':
                raise UserError("Purchase Tracking stage is not cleared yet.")
        return super(Picking, self).button_validate()
    
class Move(models.Model):
    _inherit = 'stock.move'
    
    receipt_remarks_id = fields.Many2one('receipt.remarks', "Remarks")
    truck_number = fields.Char("Truck Number")
    
    @api.onchange('quantity_done')
    def onchange_quantity_done(self):
        if self.quantity_done:
            if self.quantity_done > self.product_uom_qty:
                raise UserError(_('Done qty cannot be greater than demand.'))
    
class Partner(models.Model):
    _inherit = 'res.partner'
    
    pan = fields.Char("Pan No.")
    cha = fields.Boolean("CHA")
    cfs = fields.Boolean("CFS")
    
    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            if self.state_id.code != '08':
                fp = self.env['account.fiscal.position'].search([('name', '=', 'Inter State')], limit=1)
                if fp:
                    self.property_account_position_id = fp.id
            if self.state_id.code == '08':
                self.property_account_position_id = False
    
    
class ReceiptRemarks(models.Model):
    _name = 'receipt.remarks'
    _description = 'Receipt Remarks'
    
    name = fields.Char("Remark")
    
class Linear(models.Model):
    _name = 'linear'
    _description = 'Liner'
    
    name = fields.Char("Name")
    
class CHA(models.Model):
    _name = 'cha'
    _description = 'CHA'
    
    name = fields.Char("Name")
    
class CFS(models.Model):
    _name = 'cfs'
    _description = 'CFS'
    
    name = fields.Char("Name")
    
class ImportStage(models.Model):
    _name = 'import.stage'
    _description = 'Import Stage'
    
    sequence = fields.Integer("Sequence")
    name = fields.Char("Name")
    
class PaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    
    # team_id = fields.Many2one(comodel_name="purchase.team", string="Purchase Type")
    
    
class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    qty_pending = fields.Float('Qty Pending', readonly=True)

    def _select(self):
        return super(PurchaseReport, self)._select() + ", (sum(l.product_qty / line_uom.factor * product_uom.factor) - sum(l.qty_received / line_uom.factor * product_uom.factor)) as qty_pending"

    

    
    
    
    