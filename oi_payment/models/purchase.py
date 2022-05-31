from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    payment_detail_ids = fields.One2many('payment.details', 'purchase_order_id',"Payment Details")
    
    # @api.model
    # def create(self, vals):
    #     company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
    #     # Ensures default picking type and currency are taken from the right company.
    #     self_comp = self.with_company(company_id)
    #     if vals.get('name', 'New') == 'New':
    #         seq_date = None
    #         if 'date_order' in vals:
    #             seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
    #         vals['name'] = self_comp.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'
    #     vals, partner_vals = self._write_partner_values(vals)
    #     res = super(PurchaseOrder, self_comp).create(vals)
    #     if partner_vals:
    #         res.sudo().write(partner_vals)  # Because the purchase user doesn't have write on `res.partner`
    #     return res
            
    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        # Ensures default picking type and currency are taken from the right company.
        self_comp = self.with_company(company_id)        
        company = self.env['res.company'].browse(vals.get('company_id'))
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = 'NPO/' + company.code + '/' + self_comp.env['ir.sequence'].next_by_code('purchase.order', sequence_date=seq_date) or '/'
        vals, partner_vals = self._write_partner_values(vals)
        res = super(PurchaseOrder, self).create(vals)
        if res.payment_term_id:
            payterm_vals = []
            if res.payment_detail_ids:
                for pay in res.payment_detail_ids:
                    pay.sudo().unlink()
            if res.message_follower_ids:
                for line in res.message_follower_ids:
                    line.sudo().unlink()
            for line in res.payment_term_id.line_ids:
                payterm_vals.append(Command.create({
                        'payment_term_id': res.payment_term_id.id,
                        'payment_term_line_id': line.id,
                    }))
            res.update({'payment_detail_ids': payterm_vals})
        return res
    
    def write(self, vals):
        result = super(PurchaseOrder, self).write(vals)
        res = self
        if res.message_follower_ids:
            for line in res.message_follower_ids:
                line.sudo().unlink()
        if 'payment_term_id' in vals:
            if res.payment_term_id:
                payterm_vals = []
                if res.payment_detail_ids:
                    for pay in res.payment_detail_ids:
                        pay.sudo().unlink()
                for line in res.payment_term_id.line_ids:
                    payterm_vals.append(Command.create({
                            'payment_term_id': res.payment_term_id.id,
                            'payment_term_line_id': line.id,
                        }))
                res.update({'payment_detail_ids': payterm_vals})
        return result
        
    
    
