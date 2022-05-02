from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, html_keep_url, is_html_empty


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    
    def _timesheet_create_project(self):
        """ Generate project for the given so line, and link it.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        self.ensure_one()
        values = self._timesheet_create_project_prepare_values()
        if self.product_id.project_template_id:
            values['name'] = "%s - %s - %s" % (values['name'], self.product_id.project_template_id.name, self.order_id.partner_id.name)
            project = self.product_id.project_template_id.copy(values)
            project.tasks.write({
                'sale_line_id': self.id,
                'partner_id': self.order_id.partner_id.id,
                'email_from': self.order_id.partner_id.email,
            })
            # duplicating a project doesn't set the SO on sub-tasks
            project.tasks.filtered(lambda task: task.parent_id != False).write({
                'sale_line_id': self.id,
                'sale_order_id': self.order_id,
            })
        else:
            project = self.env['project.project'].create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        # link project as generated by current so line
        self.write({'project_id': project.id})
        return project



class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    
    
    @api.depends('order_line.price_total')
    def _amount_all_proforma(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.payment_detail_ids:
                amount_untaxed += line.subtotal_price
                amount_tax += line.tax_price
            order.update({
                'proforma_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'proforma_total': amount_untaxed + amount_tax,
            })

    payment_detail_ids = fields.One2many('payment.details', 'sale_order_id',"Payment Details")
    project_number = fields.Char(string="Project No", copy=False, compute='compute_project_number')
    all_product_delivery = fields.Boolean("All product to be delivered at a time?")
    proforma_total = fields.Float("Proforma Total", compute='_amount_all_proforma')
    proforma_untaxed = fields.Float("Proforma SubTotal", compute='_amount_all_proforma')
    tax_totals_json1 = fields.Char(compute='_compute_tax_totals_json1')
    price_basis = fields.Char("Price Basis")
    
    @api.depends('payment_detail_ids.tax_id', 'payment_detail_ids.amount', 'proforma_total', 'proforma_untaxed')
    def _compute_tax_totals_json1(self):
        def compute_taxes1(payment_detail_ids):
            price = payment_detail_ids.amount * payment_detail_ids.qty
            order = payment_detail_ids.sale_order_id
            return payment_detail_ids.tax_id._origin.compute_all(price, order.currency_id, 1, product=False, partner=order.partner_shipping_id)

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.payment_detail_ids, compute_taxes1)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.proforma_total, order.proforma_untaxed, order.currency_id)
            
            order.tax_totals_json1 = json.dumps(tax_totals)
    
    
    @api.depends('project_ids', 'project_ids.project_number')
    def compute_project_number(self):
        for rec in self:
            if rec.project_ids:
                rec.project_number = rec.project_ids[0].project_number
            else:
                rec.project_number = ''
            
               
    @api.model
    def create(self, vals):        
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            if 'warehouse_id' in vals:
                warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
                seq = self.env['ir.sequence'].next_by_code(warehouse.sale_sequence.code, sequence_date=seq_date) or _('New')
                vals['name'] = seq        
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
    actual_amount = fields.Monetary("Actual Amount", compute='compute_actual_amount', store=True)
    balance_amount = fields.Monetary("Balance Amount", compute='compute_balance_amount', store=True)
    amount_total = fields.Monetary(related='sale_order_id.amount_total', store=True)
    description = fields.Char("Description")
    qty = fields.Float("Qty")
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    amount = fields.Float("Amount")
    tax_price = fields.Float("Tax Price", compute='_compute_tax')
    total_price = fields.Float("Total Price", compute='_compute_tax')
    subtotal_price = fields.Float("SubTotal Price", compute='_compute_tax')
    hsn_code = fields.Char("HSN Code")
    product_uom = fields.Many2one('uom.uom', string='UoM')
    
    @api.depends('amount', 'tax_id')
    def _compute_tax(self):
        for line in self:
            taxes = line.tax_id.compute_all(line.qty * line.amount, line.sale_order_id.currency_id, 1, product=False, partner=line.sale_order_id.partner_shipping_id)
            line.update({
                'tax_price': taxes['total_included'] - taxes['total_excluded'],
                'total_price': taxes['total_included'],
                'subtotal_price': taxes['total_excluded'],
            })

    
    
    @api.depends('amount_total', 'payment_term_line_id', 'payment_term_line_id.value_amount')
    def compute_actual_amount(self):
        for rec in self:
            if rec.payment_term_line_id and rec.payment_term_line_id.value_amount and rec.amount_total:
                if rec.payment_term_line_id.value_amount > 0.0:
                    rec.actual_amount = rec.payment_term_line_id.value_amount
                    
    @api.depends('payment_amount', 'actual_amount', 'payment_term_line_id.value_amount')
    def compute_balance_amount(self):
        for rec in self:
            rec.balance_amount = rec.actual_amount - rec.payment_amount
                
            
    
class Payterm(models.Model):
    _inherit = "account.payment.term.line"    
    
    def name_get(self):
        result = []
        string = ''
        for line in self:
            if line.name and line.desc:
                name = line.name + line.desc
            else:
                name =  ''
            result.append((line.id, name))
        return result
    
    value = fields.Selection([
            ('balance', 'Balance'),
            ('percent', 'Percent'),
            ('fixed', 'Fixed Amount')
        ], string='Type', required=True, default='fixed',
        help="Select here the kind of valuation related to this payment terms line.")    
    supply = fields.Char("Heading")
    name = fields.Char("Percentage")
    desc = fields.Char("Description")
    supply_amount = fields.Float("Amount")
    percentage = fields.Float("Percentage")
    
    @api.onchange('supply_amount', 'percentage')
    def onchange_percentage(self):
        self.value_amount = self.supply_amount * (self.percentage /100)
    
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
    fd_amount = fields.Float(string="FD Amount", related='fixed_deposit.fd_amount', store=True)
    bg_liean_amount = fields.Float("BG Liean Amount")
    balance = fields.Float(string="Balance", related='fixed_deposit.balance', store=True)
    fixed_deposit = fields.Many2one('fixed.deposit', "Fixed Deposit")
    
    
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
    
class Warehouse(models.Model):
    _inherit='stock.warehouse'

    sale_sequence = fields.Many2one('ir.sequence','Sale Sequence')
    rep_code = fields.Char("Report Code", size=1)
    
class FixedDeposit(models.Model):
    _name = "fixed.deposit" 
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fixed Deposit"   
    
    name = fields.Char("FD Number")
    fd_amount = fields.Float("FD Amount")
    balance = fields.Float("Available Amount", compute='compute_amount_all', store=True)
    used = fields.Float("Used Amount", compute='compute_amount_all', store=True)
    bank = fields.Char("Bank")
    date = fields.Date("Date of Issue")
    maturity_date = fields.Date("Maturity Date")
    maturity_amount = fields.Float("Maturity Amount")
    bg_ids = fields.One2many('bank.guarantee', 'fixed_deposit', "BGs")
    state = fields.Selection([('running', 'Running'),('closed', 'Closed')], default='running')
    user_id = fields.Many2one('res.users', copy=False, tracking=True, string='Salesperson', default=lambda self: self.env.user)
    
    def action_view_bg(self):
        self.ensure_one()
        action = self.env.ref("oi_payment.action_bank_guarantee")
        result = action.read()[0]
        result["domain"] = [("fixed_deposit", "=", self.id)]
        result["context"] = {
            "default_fixed_deposit": self.id,
        }
        return result
    
    
    
    @api.depends('bg_ids', 'bg_ids.bg_liean_amount', 'fd_amount')
    def compute_amount_all(self):
        used = 0.0
        for rec in self:            
            if rec.bg_ids:
                for line in rec.bg_ids:
                    used += line.bg_liean_amount
            rec.used = used
            rec.balance = rec.fd_amount - used
