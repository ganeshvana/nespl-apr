from odoo import api, fields, models, tools, _


class product_pricelist(models.Model):
    _inherit = "product.pricelist"


    partner_id = fields.Many2one('res.partner',string="Partner", copy=False)
    


