from odoo import api, exceptions, fields, models, _
from datetime import datetime
from odoo.exceptions import Warning

class ProductCategory(models.Model):
    _inherit = "product.category"
    
    warranty_config_id = fields.Many2one('product.warranty.config','Warranty Configuration')
    warranty_period = fields.Integer("Enter Warranty Period",related='warranty_config_id.warranty_period')
    warranty_unit = fields.Selection([('days','Days'),('month','Month'),('year','Year')],related='warranty_config_id.warranty_unit')
    warranty_sequence_id = fields.Many2one('ir.sequence',string='Warranty Sequence',related='warranty_config_id.warranty_sequence_id')
    