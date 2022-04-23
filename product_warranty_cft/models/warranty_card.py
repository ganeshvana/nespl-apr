from odoo import api, exceptions, fields, models,tools

class WarrantyCard(models.Model):
    _name = "warranty.card"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Warranty Card"
    _order = "name"
    
    name = fields.Char(string='Name')
    image = fields.Binary(string='Image',attachment=True)
    stock_move_id = fields.Many2one('stock.move')
    
    picking_id = fields.Many2one('stock.picking',related='stock_move_id.picking_id',string='Delivery Order')
    picking_code = fields.Selection(related='stock_move_id.picking_code')
    user_id = fields.Many2one('res.users',string='Creator')

    partner_id = fields.Many2one('res.partner',related='picking_id.partner_id',string='Partner')

    sale_line_id = fields.Many2one('sale.order.line',string='Sale Order Line',related='stock_move_id.sale_line_id')
    purchase_line_id = fields.Many2one('purchase.order.line',string='Purchase Order Line',related='stock_move_id.purchase_line_id')

    sale_order_id = fields.Many2one('sale.order',related='sale_line_id.order_id',string='Sale Order')
    purchase_order_id = fields.Many2one('purchase.order',related='purchase_line_id.order_id',string='Purchase Order')

    validity_from = fields.Date(string='Validity From')
    validity_to = fields.Date(string='Validity To')    
    product_id = fields.Many2one("product.product",string="Product",related="stock_move_id.product_id")
    product_tmpl_id = fields.Many2one('product.template',string='Product Template',related='product_id.product_tmpl_id')

    notes = fields.Text(string='Notes')
    purchase_date = fields.Datetime(string='Date of Purchase')
    claim_line_ids = fields.One2many('claim.warranty','warranty_card_id',string='Claim')
    claim_count = fields.Integer(string='Claim count', compute='_compute_claim_lines_ids')
    company_id = fields.Many2one('res.company',string='Company',default=lambda self: self.env.user.company_id)
    
    
    def action_view_claim_lines(self):
        action = self.env.ref('product_warranty_cft.action_view_warranty_claim_cft').read()[0]
        claim_lines = self.mapped('claim_line_ids')
        if len(claim_lines) > 1:
            action['domain'] = [('id', 'in', claim_lines.ids)]
        elif claim_lines:
            action['views'] = [(self.env.ref('product_warranty_cft.view_warranty_claim_cft_form').id, 'form')]
            action['res_id'] = claim_lines.id
        return action

    @api.depends('claim_line_ids')
    def _compute_claim_lines_ids(self):
        for rec in self:
            rec.claim_count = len(rec.claim_line_ids)

    
class ClaimWarranty(models.Model):
    _name ='claim.warranty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Warranty Claim"
    _order = "name"

    date_of_claim = fields.Date(string='Date of Claim')
    name = fields.Char(string='Name')
    issue = fields.Char(string='Problem in Product')
    expected_delivery_date = fields.Date(string="which date it  will be repaired?")
    warranty_card_id = fields.Many2one('warranty.card',string='Warranty Card')
    product_id = fields.Many2one('product.product',string='Product',related='warranty_card_id.product_id')
    date_of_purchase = fields.Datetime(string='Date of Purchase',related='warranty_card_id.purchase_date')
    warranty_start_date = fields.Date(string='Warranty Start Date',related='warranty_card_id.validity_from')
    end_date_of_warranty = fields.Date(string='End Date of Warranty',related='warranty_card_id.validity_to')
    partner_id = fields.Many2one('res.partner',string='Partner',related='warranty_card_id.partner_id')
    remarks = fields.Char(string='Remarks')
    notes = fields.Text('Notes')
    fee_type = fields.Selection([('free','Free'),('paid','Paid')],string='Charges')
    state = fields.Selection([('draft','New'),('processing','Reparing/Processing'),('cancel','Cancel'),('done','Done')],string='Status',default='draft')
    invoice_ids = fields.One2many('account.move','claim_id',string='Invoices')
    invoice_count = fields.Integer(string='Invoice Count',compute='_compute_invoice_ids')

    
    def action_view_invoices(self):
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        invoice_ids = self.mapped('invoice_ids')
        if len(invoice_ids) > 1:
            action['domain'] = [('id', 'in', invoice_ids.ids)]
        elif invoice_ids:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoice_ids.id
        return action

    @api.depends('invoice_ids')
    def _compute_invoice_ids(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)
            
    
    def start_processing(self):
        self.state='processing'
        return True

    
    def set_to_cancel(self):
        self.state='cancel'
        return True

    
    def set_to_done(self):
        self.state='done'
        return True
    
    
    def reset_to_draft(self):
        self.state='draft'
        return True


    
    def create_draft_invoice(self):
        
        invoice_id = self.env['account.move'].create({'partner_id':self.partner_id.id,
                        'ref':self.name+'_'+self.warranty_card_id.name,
                        'state':'draft',
                        'claim_id':self.id
                        })
        return {
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': self.env.ref('account.view_move_form').id,
                'type': 'ir.actions.act_window',
                'res_id': invoice_id.id,
                }