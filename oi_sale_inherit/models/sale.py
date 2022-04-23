from odoo import api, fields, models, tools, _


class stock_picking(models.Model):
    _inherit = "stock.picking"   

    project_number = fields.Char(string="Project No", copy=False, related='sale_id.project_number')
    


