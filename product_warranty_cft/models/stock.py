from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"

    warranty_ids = fields.One2many('warranty.card', 'picking_id', string='Warranty Lines')
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
        for picking in self:
            picking.warranty_count = len(picking.warranty_ids)


class StockMove(models.Model):
    _inherit='stock.move'

    warranty_set_in_product = fields.Boolean(compute='get_warranty_seq_is_set')   
    
    
    def get_warranty_seq_is_set(self):
        configs = self.env['product.warranty.config'].search([])
        Flag = False
        for conf in configs:            
            if conf.applied_on=='3_global':
                Flag = True
                break
        if Flag:
            for line in self:
                line.warranty_set_in_product= True
            return True
        for line in self:
            product =line.product_id
            if product.warranty_config_id or product.product_tmpl_id.warranty_config_id or product.categ_id.warranty_config_id:
                line.warranty_set_in_product= True
            else:
                line.warranty_set_in_product=False
        return True

    
    @api.depends('name')
    def name_get(self):
        result = []
        if self.env.context.get('move_for_warranty'):
            for move in self:
                new_name= move.sale_line_id.order_id.name or move.purchase_line_id.order_id.name or move.picking_id.name or ''
                name = move.product_id.name + '_' + new_name
                result.append((move.id, name))
        else:
            result = super(StockMove,self).name_get()

        return result
    
