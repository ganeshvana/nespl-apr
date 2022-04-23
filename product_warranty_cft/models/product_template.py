from odoo import api, exceptions, fields, models, _
from datetime import datetime
from odoo.exceptions import Warning

class ProductProduct(models.Model):
    _inherit = "product.template"
    
    warranty_config_id = fields.Many2one('product.warranty.config')
    warranty_ids = fields.One2many('warranty.card','product_tmpl_id',string='Warranty Entries')
    warranty_count = fields.Integer(string='Warranty count', compute='_compute_warranty_lines_ids')

    
    def action_view_warranty_lines(self):
        action = self.env.ref('product_warranty_cft.action_view_warranty_card_cft').read()[0]
        warranty_lines = self.mapped('warranty_ids')
        if len(warranty_lines) > 1:
            action['domain'] = [('id', 'in', warranty_lines.ids)]
        elif warranty_lines:
            action['views'] = [(self.env.ref('product_warranty_cft.view_warranty_card_cft_form').id, 'form')]
            action['res_id'] = warranty_lines.id
        return action

    @api.depends('warranty_ids')
    def _compute_warranty_lines_ids(self):
        for template in self:
            template.warranty_count = len(template.warranty_ids)

class ProductProduct(models.Model):
    _inherit = "product.product"

    warranty_config_id = fields.Many2one('product.warranty.config')
    warranty_ids = fields.One2many('warranty.card','product_id',string='Warranty Entries')
    warranty_count = fields.Integer(string='Warranty count', compute='_compute_warranty_lines_ids')

    @api.depends('warranty_ids')
    def _compute_warranty_lines_ids(self):
        for template in self:
            template.warranty_count = len(template.warranty_ids)

    
    def action_view_warranty_lines(self):
        action = self.env.ref('product_warranty_cft.action_view_warranty_card_cft').read()[0]
        warranty_lines = self.mapped('warranty_ids')
        if len(warranty_lines) > 1:
            action['domain'] = [('id', 'in', warranty_lines.ids)]
        elif warranty_lines:
            action['views'] = [(self.env.ref('product_warranty_cft.view_warranty_card_cft_form').id, 'form')]
            action['res_id'] = warranty_lines.id
        return action