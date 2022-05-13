from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class stock_picking(models.Model):
    _inherit = "stock.picking"   

    project_number = fields.Char(string="Project No")
    reference_number = fields.Char(string="Reference", copy=False)
    client_po_no = fields.Char(string="Client PO No ", copy=False)
    client_date = fields.Char(string="Clinet PO Date ", copy=False)
    material_insured1 = fields.Selection([('Yes', 'Yes'), ('No', 'NO')], string="Material Insured", copy=False)
    insurance_policy = fields.Char(string="Insurance Policy ", copy=False)
    insurance_number = fields.Char(string="Insurance Number", copy=False)
    transport_mode = fields.Selection([('road', 'Road'), ('air', 'Air'), ('sea', 'Sea')], string="Mode Of Transport", copy=False)
    transport = fields.Selection([('courier', 'Courier'),('truck', 'Truck')], string="Truck / Courier", copy=False)
    loading = fields.Char(string="Place Of Loading", copy=False)
    discharge = fields.Char(string="Place Of Discharge", copy=False)
    truck_number = fields.Char("Truck Number")
    price_basis = fields.Char("Price Basis")
    transporter = fields.Char("Transporter")
    lr = fields.Char("LR No.")
    booked_by = fields.Char("Booked by")
    vehicle_type = fields.Char("Vehicle Type")
    courier = fields.Char("Courier Name")
    tracking = fields.Char("Tracking ID")
    contact_person = fields.Char("Contact Person")
    contact_person_number = fields.Char("Contact Person Mobile")
    address_id = fields.Many2one('res.partner', "Address")
    
    def button_validate(self):
        res = super(stock_picking, self).button_validate()
        if self.sale_id:
            if self.sale_id.all_product_delivery == True:
                not_done_full = any(line.quantity_done == 0 for line in self.move_ids_without_package)
                if not_done_full:
                    raise UserError(_('All Items should be shipped at once for this Delivery.'))
        return res
    
    # def create(self, vals):     
    #     res = super(stock_picking, self).create(vals)
    #     if res.company_id:
    #         res.address_id = res.company_id.partner_id.id
    #     if res.sale_id:
    #         res.project_number = res.sale_id.project_number
    #     if res.message_follower_ids:
    #         for line in res.message_follower_ids:
    #             line.sudo().unlink()
    #     return res
    
    # def write(self, vals):     
    #     res = super(stock_picking, self).write(vals)
    #     res = self
    #     if res.message_follower_ids:
    #         for line in res.message_follower_ids:
    #             line.sudo().unlink()
    #     return res

