from odoo import api, fields, models, tools, _


class product_pricelist(models.Model):
    _inherit = "product.pricelist"


    partner_id = fields.Many2one('res.partner',string="Partner", copy=False)
    
class SO(models.Model):
    _inherit = "sale.order"
    
    bank = fields.Many2one('res.partner.bank')
    
class SOL(models.Model):
    _inherit = "sale.order.line"
    
    pi = fields.Boolean("PI")
    
class Bank(models.Model):
    _inherit = "res.bank"
    
    micr = fields.Char("MICR Code")
    


