from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class stock_picking(models.Model):
    _inherit = "stock.picking"   

    project_number = fields.Char(string="Project No", related='sale_id.project_number')
    reference_number = fields.Char(string="Reference", copy=False)
    client_po_no = fields.Char(string="Client PO No ", copy=False)
    client_date = fields.Char(string="Clinet PO Date ", copy=False)
    material_insured = fields.Selection([('yes', 'Yes'), ('no', 'NO')], string="Material Insured", copy=False)
    insurance_policy = fields.Char(string="Insurance Policy ", copy=False)
    insurance_number = fields.Char(string="Insurance Number", copy=False)
    transport = fields.Selection([('road', 'Road'), ('air', 'Air'), ('sea', 'Sea')], string="Mode Of Transport", copy=False)
    loading = fields.Char(string="Place Of Loading", copy=False)
    truck_number = fields.Char("Truck Number")
    
    def button_validate(self):
        res = super(stock_picking, self).button_validate()
        if self.sale_id:
            if self.sale_id.all_product_delivery == True:
                not_done_full = any(line.quantity_done == 0 for line in self.move_ids_without_package)
                if not_done_full:
                    raise UserError(_('All Items should be shipped at once for this Delivery.'))
        return res
    


