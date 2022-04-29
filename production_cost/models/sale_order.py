# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.tools import is_html_empty
from datetime import datetime, timedelta

default_content = '''
<p>Dear Sir/Madam,<br/>
With reference to your discussions with our team.<br/>
We are pleased to quote our competitive offer for your requirements.<br/>
Look forward to receiving your valuable business.<br/>
Please feel free to revert in case of any queries.<br/>
Thanking you and assuring you of our best service.<br/><br/>
Yours faithfully,<br/></p>

 '''

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    entry_count = fields.Integer(string='Entry Count', compute='count_entry')
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    project_costing_id = fields.Many2one('product.entry', "Costing")
    costing_structure_ids = fields.One2many(related='project_costing_id.costing_structure_ids',)
    
    @api.onchange('employee_pin', 'employee_id')
    def onchange_employee_pin(self):
        if self.employee_pin and not self.employee_id:
            raise ValidationError("Select Employee")
        # if self.employee_pin and self.employee_id:
        #     if self.employee_pin != self.employee_id.employee_pin:
        #         raise ValidationError("PIN is wrong!!!")
        
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        for rec in self:
            if rec.employee_id and not rec.employee_pin:
                raise ValidationError("Enter Employee PIN !!!")
            if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
                raise ValidationError("PIN is wrong!!!")
            if 'employee_pin' in vals:
                if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
                    raise ValidationError("PIN is wrong!!!")
        return res
    
    def action_view_bom(self):
        self.ensure_one()
        view_form_id = self.env.ref('sale_management.sale_order_template_view_form').id
        bom = self.env['sale.order.template'].search([('sale_order_id', '=', self.id)], limit=1)
        print(bom)
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'name': _('BoM'),
            'res_model': 'sale.order.template',
            'domain': [('id', '=', bom.id)]
        }
        
        if bom:
            action.update({'views': [(view_form_id, 'form')], 'res_id': bom.id})
        else:
            action.update({'views': [(view_form_id, 'form')], 'res_id': self.sale_order_template_id.id, 'context': {'default_sale_order_id': self.id}})
        return action
    
    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):

        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return

        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        # --- first, process the list of products from the template
        order_lines = [(5, 0, 0)]
        for line in template.sale_order_template_line_ids:
            data = self._compute_line_data_for_template_change(line)
            if line.product_id:
                price = line.product_id.lst_price
                discount = 0

                if self.pricelist_id:
                    pricelist_price = self.pricelist_id.with_context(uom=line.product_uom_id.id).get_product_price(line.product_id, 1, False)

                    if self.pricelist_id.discount_policy == 'without_discount' and price:
                        discount = max(0, (price - pricelist_price) * 100 / price)
                    else:
                        price = pricelist_price

                data.update({
                    'price_unit': line.cost,
                    'discount': discount,
                    'product_uom_qty': line.product_uom_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'customer_lead': self._get_customer_lead(line.product_id.product_tmpl_id),
                })

            order_lines.append((0, 0, data))

        self.order_line = order_lines
        self.order_line._compute_tax_id()

        # then, process the list of optional products from the template
        option_lines = [(5, 0, 0)]
        for option in template.sale_order_template_option_ids:
            data = self._compute_option_data_for_template_change(option)
            option_lines.append((0, 0, data))

        self.sale_order_option_ids = option_lines

        if template.number_of_days > 0:
            self.validity_date = fields.Date.context_today(self) + timedelta(template.number_of_days)

        self.require_signature = template.require_signature
        self.require_payment = template.require_payment

        if not is_html_empty(template.note):
            self.note = template.note


    def unlink(self):
        return super(SaleOrder, self).unlink()

    def count_entry(self):
        for order in self:
            entry_ids = self.env['product.entry'].search([('sale_order_id', '=', order.id)])
            order.entry_count = len(entry_ids) if entry_ids else 0

    def view_product_entry(self):
        entry_ids = self.env['product.entry'].search([('sale_order_id', 'in', self.ids)])
        return {
            'name': _('Product Entry'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.entry',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', entry_ids.ids)],
        }
        
class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'
    
    kw = fields.Float("KWP")
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], default='draft', copy=False)
    sale_order_id = fields.Many2one('sale.order', "Sale Order")
    partner_id = fields.Many2one('res.partner')
    opex_lines = fields.One2many('opex.lines', 'template_id', "OPEX")
    opex_lines_site = fields.One2many('opex.lines.site', 'template_id', "OPEX Sites")
    opex_lines_site_rate = fields.One2many('opex.lines.site.year', 'template_id', "OPEX")
    opex_description = fields.Html("Summary")
    subject = fields.Char("Subject")
    reference = fields.Char("Reference")
    content = fields.Html("Content", default=default_content, copy=True)
    project_costing_id = fields.Many2one('product.entry', "Costing")
    costing_structure_ids = fields.One2many(related='project_costing_id.costing_structure_ids',)
    
    
    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self.env.ref('production_cost.email_template_bom2')
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        
        ctx = {
            'default_model': 'sale.order.template',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id.id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

class SaleOrderTemplateLine(models.Model):
    _inherit = 'sale.order.template.line'
    
    unit = fields.Float("Unit")
    per_kw = fields.Float("Per KW", compute='compute_per_kw', store=True)
    kw = fields.Float(related='sale_order_template_id.kw', store=True)
    cost = fields.Float("Cost")
    total = fields.Float("Total")
    partner_ids = fields.Many2many('res.partner', 'vendor_template_rel1', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_rel', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    hide = fields.Boolean("Hide")
    type = fields.Selection([('bom', 'BoM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC')], default='bom')
    name1 = fields.Char("Name")
    
    @api.onchange('name')
    def onchange_name(self):
        self.name1 = self.name
    
    @api.onchange('product_id')
    def onchange_product(self):
        products = []
        if self.product_id:
            if self.product_id.seller_ids:
                for line in self.product_id.seller_ids:
                    products.append(line.name.id)
            self.partner_ids = [(6, 0, products)]
    
    @api.depends('kw', 'unit')
    def compute_per_kw(self):
        for rec in self:
            if rec.unit > 0.0:
                rec.per_kw = (rec.kw * 1000)/rec.unit
                
class SaleOrderTemplateOption(models.Model):
    _inherit = 'sale.order.template.option'
    
    unit = fields.Float("Unit")
    per_kw = fields.Float("Per KW", compute='compute_per_kw', store=True)
    kw = fields.Float(related='sale_order_template_id.kw', store=True)
    cost = fields.Float("Cost")
    total = fields.Float("Total")
    partner_ids = fields.Many2many('res.partner', 'vendor_template_rel2', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_rel22', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    hide = fields.Boolean("Hide")
    type = fields.Selection([('bom', 'BoM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC')], default='bom')
    
    @api.onchange('product_id')
    def onchange_product(self):
        products = []
        if self.product_id:
            if self.product_id.seller_ids:
                for line in self.product_id.seller_ids:
                    products.append(line.name.id)
            self.partner_ids = [(6, 0, products)]
    
    @api.depends('kw', 'unit')
    def compute_per_kw(self):
        for rec in self:
            if rec.unit > 0.0:
                rec.per_kw = (rec.kw * 1000)/rec.unit
                
class OpexLines(models.Model):
    _name = 'opex.lines'
    _description = "Opex Lines"
    _order = 'sequence'
    
    template_id = fields.Many2one('sale.order.template', "Template")
    particular = fields.Html("Particular")
    offered = fields.Html("Offered")
    sequence = fields.Integer("Sequence")
    
    
class OpexLinesSite(models.Model):
    _name = 'opex.lines.site'
    _description = "Opex Lines Site"
    _rec_name = 'plant_name'
    
    template_id = fields.Many2one('sale.order.template', "Template")
    plant_name = fields.Char("Plant Name")
    buyer_location = fields.Char("Buyer Location")
    solar_capacity = fields.Char("Offered Solar Capacity KWp (DC)")
    output_voltage = fields.Char("Solar System Output Voltage")
    buyer_contract = fields.Char("Buyer Contract Demand / Sanction Load (KVA)")
    buyer_grid = fields.Char("Buyer grid connection Voltage (KV)")
    
class OpexLinesSiteYear(models.Model):
    _name = 'opex.lines.site.year'
    _description = "Opex Lines Site Year"
    
    template_id = fields.Many2one('sale.order.template', "Template")
    site_id = fields.Many2one('opex.lines.site', "Site")
    particular = fields.Char("Particular")
    year = fields.Char("Tenure of Agreement")
    rate = fields.Float("Rate Rs. / Kwh")
