from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    payment_detail_ids = fields.One2many('payment.details', 'sale_order_id',"Payment Details")
            
    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
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
        if res.team_id.name == 'Website':
            lead = self.env['crm.lead'].search([('type','=','opportunity')], order='id desc', limit=1)
            if lead:
                res.opportunity_id = lead.id
                res.partner_id = lead.partner_id.id
        return res
    
    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        res = self
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
    
    def open_cart_detail(self):
        self.website_id.sale_order_id = self.id
        self.action_draft()
        baseurl = self.env.company.get_base_url() + '/shop/cart?access_token=' + self.access_token
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': baseurl,
            'target': 'new',
        }
        
    
    
class PaymentDetails(models.Model):
    _name = 'payment.details'
    _description = 'Payment Details'
    
    sale_order_id = fields.Many2one('sale.order', "Sale Order")
    purchase_order_id = fields.Many2one('purchase.order', "Purchase Order")
    payment_term_id = fields.Many2one('account.payment.term', "Payment Term")
    payment_term_line_id = fields.Many2one('account.payment.term.line', "Milestone")
    payment_ids = fields.Many2many('account.payment', 'payment_sale_rel', 'pay_id', 'sale_id', "Payment")
    currency_id = fields.Many2one(related='sale_order_id.currency_id', string="Currency")
    payment_amount = fields.Monetary("Payment Amount")
    
class Payterm(models.Model):
    _inherit = "account.payment.term.line"    
    
    def name_get(self):
        result = []
        string = ''
        for line in self:
            if line.value:
                if line.value == 'balance':
                    string = 'Balance'
                if line.value == 'percent':
                    string = str(line.value_amount) + ' Percentage'                    
                if line.value == 'fixed':
                    string = str(line.value_amount) + ' Fixed'  
                name =  string
            else:
                name =  'Payment Term Line'
            result.append((line.id, name))
        return result
    
