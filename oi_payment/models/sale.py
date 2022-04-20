from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta


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
    
class BankGuarantee(models.Model):
    _name = "bank.guarantee" 
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bank Guarantee"   
    
    state = fields.Selection([('draft', 'Draft'),('inprogress', 'In progress'),('validate', 'Validated')], default='draft')
    date = fields.Date("Date", default=fields.Date.today())
    partner_id = fields.Many2one('res.partner', "Customer")
    name = fields.Char("BG Number")
    expiry_date = fields.Date("BG Expiry Date")
    claim_expiry_date = fields.Date("Claim Expiry Date")
    amount = fields.Float("BG Amount")
    remarks = fields.Text("Remarks")
    fd_no = fields.Char("FD No.")
    fdremarks = fields.Text("Remarks")
    bgtype_id = fields.Many2one('bank.guarantee.type', "BG Type")    
    activity_created = fields.Boolean("Activity Created")    
    user_id = fields.Many2one('res.users', copy=False, tracking=True, string='Salesperson', default=lambda self: self.env.user)
    
    def get_expiring_bg(self):
        late_payment_po = []
        template_rec = False
        users = []
        guarantees = self.env['bank.guarantee'].search([('state', '=', 'inprogress'),('activity_created', '=', False)])
        if guarantees:
            for gua in guarantees:
                if gua.expiry_date + timedelta(days=-7) == fields.Date.today():  
                    body_dynamic_html = '<p> Bank Guarantee %s is expiring on %s </p></div>'%(gua.name, gua.expiry_date)                   
                    activity_type = self.env['mail.activity.type'].search([('name','=','To Do')])
                    modell = self.env['ir.model'].search([('model', '=', 'bank.guarantee')])
                    user = gua.user_id
                    mail_activity = self.env['mail.activity'].create({
                        'activity_type_id': activity_type.id,
                        'summary': 'Guaranty Expiry',
                        'date_deadline': fields.Date.today(),
                        'user_id': user.id,
                        'note': body_dynamic_html,
                        'res_model': 'bank.guarantee',
                        'res_id': gua.id,
                        'res_model_id': modell.id,
                        })
                    gua.activity_created = True   
                    self.env.cr.commit()
                    
                                         
        return True
    
class BankGuaranteeType(models.Model):
    _name = "bank.guarantee.type" 
    _description = "Bank Guarantee Type" 
    
    name = fields.Char("Name")
    
