from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class stock_picking(models.Model):
    _inherit = "stock.picking"   

    project_number = fields.Char(string="Project No", copy=False, related='sale_id.project_number')
    
    def button_validate(self):
        res = super(stock_picking, self).button_validate()
        if self.sale_id:
            if self.sale_id.all_product_delivery == True:
                not_done_full = any(line.quantity_done == 0 for line in self.move_ids_without_package)
                if not_done_full:
                    raise UserError(_('All Items should be shipped at once for this Delivery.'))
        return res
    


