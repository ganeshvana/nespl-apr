from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Payment(models.Model):
    _inherit = "account.payment"
    
    sale_order_id = fields.Many2one('sale.order', "Sale Order", copy=False)
    payment_term_line_ids = fields.Many2many('account.payment.term.line', 'pricelist_payment_rel', 'pricelist_id', 'payment_id',"Milestone", copy=False)
    reference = fields.Char("Reference")
    purchase_order_id = fields.Many2one('purchase.order', "Purchase Order", copy=False)
    po_payment_term_line_ids = fields.Many2many('account.payment.term.line', 'pricelist_payment_purchase_rel', 'pricelist_id', 'payment_id',"Milestone", copy=False)
    
    
    @api.onchange('sale_order_id')
    def onchange_sale_order_id(self):
        res ={}
        pricelist_lines = []
        if self.sale_order_id:
            if self.sale_order_id.payment_detail_ids:
                for line in self.sale_order_id.payment_detail_ids:
                    pricelist_lines.append(line.payment_term_line_id.id)
            res['domain'] = {'payment_term_line_ids': [('id','in',pricelist_lines)]}
        return res
    
    @api.onchange('purchase_order_id')
    def onchange_purchase_order_id(self):
        res ={}
        pricelist_lines = []
        if self.purchase_order_id:
            if self.purchase_order_id.payment_detail_ids:
                for line in self.purchase_order_id.payment_detail_ids:
                    if not line.payment_ids:
                        pricelist_lines.append(line.payment_term_line_id.id)
            res['domain'] = {'po_payment_term_line_ids': [('id','in',pricelist_lines)]}
        return res

    def action_post(self):
        res = super(Payment, self).action_post()
        if self.payment_type == 'inbound':
            if self.sale_order_id and self.payment_term_line_ids:
                for line in self.payment_term_line_ids:
                    priceline = self.sale_order_id.payment_detail_ids.filtered(lambda m: m.payment_term_line_id.id == line.id)
                    if priceline:
                        priceline.payment_ids = [(4,self.id)]
                        priceline.payment_amount += self.amount
                mail_template_id = self.env.ref('oi_payment.mail_template_payment_received')
                self.env['mail.template'].browse(mail_template_id.id).send_mail(self.id, force_send=True)
        if self.payment_type == 'outbound':
            if self.purchase_order_id and self.po_payment_term_line_ids:
                for line in self.po_payment_term_line_ids:
                    priceline = self.purchase_order_id.payment_detail_ids.filtered(lambda m: m.payment_term_line_id.id == line.id)
                    if priceline:
                        priceline.payment_ids = [(4,self.id)]
                        priceline.payment_amount += self.amount
                # mail_template_id = self.env.ref('oi_payment.mail_template_payment_received')
                # self.env['mail.template'].browse(mail_template_id.id).send_mail(self.id, force_send=True)
        return res
            

