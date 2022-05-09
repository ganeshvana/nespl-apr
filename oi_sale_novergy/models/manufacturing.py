from odoo import api, fields, models, tools, _

class mrp_bom(models.Model):
    _inherit = "mrp.bom"

    partner_id = fields.Many2one('res.partner',string="Partner", copy=False)
    


