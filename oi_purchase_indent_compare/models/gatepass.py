from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from datetime import timedelta
from collections import defaultdict


class Gatepass(models.Model):
    _name = 'gatepass'
    _description = 'Gatepass'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    state = fields.Selection([('in', 'In'), ('out', 'Out')], "State", default='in')
    name = fields.Char("Ref")    
    date = fields.Datetime("Date", default=fields.Date.today())
    mode = fields.Char("Mode")
    contact = fields.Char("Contact")
    truck_no = fields.Char("Truck No.")
    gross_weight = fields.Float("Gross Weight")
    net_weight = fields.Float("Net Weight")
    product_id = fields.Many2one('product.product', "Product")
    partner_id = fields.Many2one('res.partner', "Vendor")
    qty = fields.Float("Qty")
    return_id = fields.Many2one('res.users', "Return By")
    return_time = fields.Datetime("Return Time")
    
    def returnpass(self):
        self.return_id = self.env.user.id
        self.return_time = fields.Datetime.now()
        self.state = 'out'
        
    
    
    @api.model
    def create(self, vals):
        res = super(Gatepass, self).create(vals)
        sequence = self.env['ir.sequence'].next_by_code('gatepass.seq')
        res.name = sequence
        return res
    
    
