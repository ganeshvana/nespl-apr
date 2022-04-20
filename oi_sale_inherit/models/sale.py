from odoo import api, fields, models, tools, _

class stock_picking(models.Model):
    _inherit = "stock.picking"

    vehicle_number = fields.Char(string="Vehicle No.", copy=False)
    so_id = fields.Many2one('sale.order','SO',compute='_get_sale')
    so_id = fields.Many2one('purchase.order','SO',compute='_get_purchase')





    @api.depends('origin')
    def _get_sale(self):
        for record in self:
            record.so_id = ''
            if record.origin:
                so_obj = self.env['sale.order'].search([('name','=',record.origin)])
                if so_obj:
                    record.so_id = so_obj.id
                else:
                    record.so_id = '' 



    @api.depends('origin')
    def _get_purchase(self):
        for record in self:
            record.so_id = ''
            if record.origin:
                so_obj = self.env['purchase.order'].search([('name','=',record.origin)])
                if so_obj:
                    record.so_id = so_obj.id
                else:
                    record.so_id = '' 
                   
   
class stock_picking(models.Model):
    _inherit = "stock.picking"   

    reference_number = fields.Char(string="Reference", copy=False)
    client_po_no = fields.Char(string="Client PO No ", copy=False)
    client_date = fields.Char(string="Clinet PO Date ", copy=False)
    material_insured = fields.Selection([('yes', 'Yes'), ('no', 'NO')], string="Material Insured", copy=False)
    insurance_policy = fields.Char(string="Insurance Policy ", copy=False)
    insurance_number = fields.Char(string="Insurance Number", copy=False)
    project_number = fields.Char(string="Project No", copy=False)
    transport = fields.Selection([('road', 'Road'), ('air', 'Air'), ('sea', 'Sea')], string="Mode Of Transport", copy=False)
    loading = fields.Char(string="Place Of Loading", copy=False)



class stock_picking(models.Model):
    _inherit = "stock.picking"   

    customer_po = fields.Char(string="Customer PO No", copy=False)
    project_id = fields.Char(string="Project ID", copy=False)
    salesman_code = fields.Char(string="Salesman Code", copy=False)
    fax = fields.Char(string="Fax", copy=False)






