from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class Move(models.Model):
    _inherit = "account.move"
    
    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        pricelist_lines = []
        sale_id = False
        purchase_id = False
        milestone = []
        sale_order = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id)])
        if sale_order:
            for sale in sale_order:
                if sale.invoice_ids:
                    if self.id in sale.invoice_ids.ids:
                        sale_id = sale.id
                        if sale_id:
                            for line in sale.payment_detail_ids:
                                if not line.payment_ids:
                                    pricelist_lines.append(line.payment_term_line_id.id)
                            if pricelist_lines:
                                milestone.append(pricelist_lines[0])
                                
        purchase_order = self.env['purchase.order'].search([('partner_id', '=', self.partner_id.id)])
        if purchase_order:
            for purchase in purchase_order:
                if purchase.invoice_ids:
                    if self.id in purchase.invoice_ids.ids:
                        purchase_id = purchase.id
                        if purchase_id:
                            for line in purchase.payment_detail_ids:
                                if not line.payment_ids:
                                    pricelist_lines.append(line.payment_term_line_id.id)
                            if pricelist_lines:
                                milestone.append(pricelist_lines[0])
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_sale_order_id': sale_id,
                'default_payment_term_line_ids': [(6, 0, milestone)],
                'default_purchase_order_id': purchase_id,
                'default_po_payment_term_line_ids': [(6, 0, milestone)]
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        
    delivery_challan_no = fields.Char("Delivery Challan No")
    delivery_challan_date = fields.Date("Delivery Challan Date")
    courier = fields.Char("Dispatch through Carrier")
    awb = fields.Char("LR / GR / Docket ? AWB No")
    friegt = fields.Char("Freight Term")
    insurance = fields.Char("Insurance")
    rep_code = fields.Char("Report Code")
    po_ref = fields.Char("PO Ref")
    project_id = fields.Many2one('project.project',"Project")

class Incoterm(models.Model):
    _inherit = "account.incoterms"
    
    amount = fields.Float("Amount")
    
    