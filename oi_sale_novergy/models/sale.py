from odoo import api, fields, models, tools, _


class product_pricelist(models.Model):
    _inherit = "product.pricelist"
    
    partner_id = fields.Many2one('res.partner',string="Partner", copy=False)
    
class SupplierInfo(models.Model):
    _inherit = "product.supplierinfo"
    
    agreement_number = fields.Char("Agreement Number")
    agreement = fields.Boolean("Agreement?")
    
    def create(self, vals_list):
        result = super(SupplierInfo, self).create(vals_list)
        for res in result:
            if res.agreement:
                seq = self.env['ir.sequence'].next_by_code('purchase.agreement.seq') or '/'
                res.agreement_number = seq   
        return result 
    
class SO(models.Model):
    _inherit = "sale.order"
    
    bank = fields.Many2one('res.partner.bank')
    
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).', self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'user_id': self.user_id.id,
            'project_id': self.project_number,
            'invoice_user_id': self.user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals
    
class SOL(models.Model):
    _inherit = "sale.order.line"
    
    pi = fields.Boolean("PI")
    
class Bank(models.Model):
    _inherit = "res.bank"
    
    micr = fields.Char("MICR Code")
    


