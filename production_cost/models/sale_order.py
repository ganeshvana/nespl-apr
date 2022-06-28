# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.tools import is_html_empty
from datetime import datetime, timedelta
import base64

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
    opex_description = fields.Html("Summary")
    subject = fields.Char("Subject")
    reference = fields.Char("Reference")
    kind_attn = fields.Char("Kind Attn.")
    content = fields.Html("Content", default=default_content, copy=True)
    opex_lines = fields.One2many('opex.lines', 'sale_order_id', "OPEX", copy=True)
    opex_lines_site = fields.One2many('opex.lines.site', 'sale_order_id', "OPEX Sites", copy=True)
    opex_lines_site_rate = fields.One2many('opex.lines.site.year', 'sale_order_id', "OPEX", copy=True)
    opex_description = fields.Html("Summary", copy=True)
    rounded_off_with_markup = fields.Float("Quoted Price")
    type = fields.Selection([('sale', 'Sale'), ('project', 'Project')], default = 'sale')
    revised_for_project = fields.Boolean("Project Revision", copy=False)
    
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
    
    def _compute_option_data_for_template_change(self, option):
        price = option.product_id.lst_price
        discount = 0

        if self.pricelist_id:
            pricelist_price = self.pricelist_id.with_context(uom=option.uom_id.id).get_product_price(option.product_id, 1, False)

            if self.pricelist_id.discount_policy == 'without_discount' and price:
                discount = max(0, (price - pricelist_price) * 100 / price)
            else:
                price = pricelist_price

        return {
            'product_id': option.product_id.id,
            'name': option.name,
            'quantity': option.quantity,
            'uom_id': option.uom_id.id,
            'price_unit': price,
            'discount': discount,
            'partner_ids': [(6,0, option.partner_ids.ids)],
            'vendor_ids': [(6,0, option.vendor_ids.ids)],
            'model': option.model,
        }
    
    @api.onchange('sale_order_template_id')
    def onchange_sale_order_template_id(self):

        if not self.sale_order_template_id:
            self.require_signature = self._get_default_require_signature()
            self.require_payment = self._get_default_require_payment()
            return

        template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        # --- first, process the list of products from the template
        self.subject = self.sale_order_template_id.subject
        self.reference = self.sale_order_template_id.reference
        self.kind_attn = self.sale_order_template_id.kind_attn
        self.content = self.sale_order_template_id.content
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
                    'partner_ids': [(6,0, line.partner_ids.ids)],
                    'vendor_ids': [(6,0, line.vendor_ids.ids)],
                    'model': line.model,
                    'hide': line.hide,
                    'model': line.model,
                    'type': line.type,
                    'per_kw' : line.cost,
                    'kwpunit': line.kwpunit,
                    'cost': line.cost,
                    'printkwp': line.printkwp,                    
                    'quotation_template_line_id': line.id
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
        
        op_lines = [(5, 0, 0)]        
        for ol in template.opex_lines:
            o_data = {}
            o_data.update({
                    'sequence': ol.sequence,
                    'particular': ol.particular,
                    'offered': ol.offered,
                })
            op_lines.append((0, 0, o_data))
        self.opex_lines = op_lines
        
        op_lines1 = [(5, 0, 0)]        
        for ol in template.opex_lines_site_rate:
            o_data2 = {}
            o_data2.update({
                    'site_id': ol.site_id,
                    'particular': ol.particular,
                    'rate': ol.rate,
                    'year': ol.year,
                })
            op_lines1.append((0, 0, o_data2))
        self.opex_lines_site_rate = op_lines1
        
        op_lines2 = [(5, 0, 0)]        
        for ol in template.opex_lines_site:
            o_data3 = {}
            o_data3.update({
                    'plant_name': ol.plant_name,
                    'buyer_location': ol.buyer_location,
                    'solar_capacity': ol.solar_capacity,
                    'output_voltage': ol.output_voltage,
                    'buyer_contract': ol.buyer_contract,
                    'buyer_grid': ol.buyer_grid,
                })
            op_lines2.append((0, 0, o_data3))
        self.opex_lines_site = op_lines2
        
        
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
        entry_ids = self.env['product.entry'].search([('sale_order_id', '=', self.id)], limit=1)
        if not entry_ids:
            entry_ids = self.env['product.entry'].create({
                'sale_order_id': self.id,
                'quotation_template_id': self.sale_order_template_id.id,
                'kw': self.kw
                })
            self.project_costing_id = entry_ids.id
            # entry_ids.onchange_quotation_template_id()
            order_lines = [(5, 0, 0)]
            option_lines = [(5, 0, 0)]
            # if entry_ids.quotation_template_id:
            if self.order_line:
                for line in self.order_line:
                    if line.product_id:
                        data = {
                            'product_uom_qty': line.product_uom_qty,
                            'product_id': line.product_id.id,
                            'name': line.name,
                            'product_uom_id': line.product_uom.id,
                            'sale_order_line_id' : line.id,
                            'type': line.type,
                            'kwp': self.kw,
                            'cost': line.cost,
                            'kw_cost': line.cost
                        }
                        order_lines.append((0, 0, data))
                for line2 in self.sale_order_option_ids:
                    if line2.product_id:
                        data = {
                            'product_uom_qty': line2.quantity,
                            'product_id': line2.product_id.id,
                            'product_uom_id': line2.uom_id.id,
                            # 'quotation_template_line_id' : line.id,
                            'kwp': self.kw
                        }
                        option_lines.append((0, 0, data))
            entry_ids.order_line = order_lines
            entry_ids.cost_lines_option = option_lines
            
        if self.project_costing_id:
            if self.project_costing_id.kw != self.kw:
                self.project_costing_id.kw = self.kw
                for l in self.project_costing_id.order_line:
                    l.kwp = self.kw
            for line3 in self.project_costing_id.order_line:
                if not line3.sale_order_line_id:
                    line3.unlink()
            for line4 in self.order_line:
                costlines = False
                costlines = self.project_costing_id.order_line.filtered(lambda l: l.product_id == line4.product_id)    
                if not costlines:
                    if line4.product_id:
                        pel = self.env['product.entry.line'].create({
                            'product_id': line4.product_id.id,
                            'name': line4.name,
                            'kwp': self.kw,
                            'cost': line4.cost,
                            'type': line4.type,
                            'entry_id': self.project_costing_id.id,
                            'sale_order_line_id': line4.id
                            })
                
        return {
            'name': _('Product Entry'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.entry',
            'view_id': False,
            'res_id': entry_ids.id,
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', entry_ids.id)],
        }
        
    def action_quotation_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
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
        
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.type == 'sale':
            for line in self.picking_ids:
                line.project = True
                line.action_cancel()
        return res
    
    def _get_new_rev_data1(self, new_rev_number):
        self.ensure_one()
        return {
            "revision_number": new_rev_number,
            "unrevisioned_name": self.unrevisioned_name,
            "name": "%s-P%02d" % (self.unrevisioned_name, new_rev_number),
            "old_revision_ids": [(4, self.id, False)],
            'type': 'project',
            'sale_order_template_id': False
        }
    
    def copy_revision_with_context1(self):
        default_data = self.default_get([])
        new_rev_number = self.revision_number + 1
        vals = self._get_new_rev_data1(new_rev_number)
        default_data.update(vals)
        new_revision = self.copy(default_data)
        self.old_revision_ids.write({"current_revision_id": new_revision.id})
        self.write(self._prepare_revision_data(new_revision))
        return new_revision
    
    def request_for_project(self):
        self.revised_for_project = True
        revision_ids = []
        for rec in self:
            copied_rec = rec.copy_revision_with_context1()
            if hasattr(self, "message_post"):
                msg = _("New revision created: %s") % copied_rec.name
                copied_rec.message_post(body=msg)
                rec.message_post(body=msg)
            revision_ids.append(copied_rec.id)
            projects = []
            if copied_rec.project_id:
                projects.append(copied_rec.project_id.id)
            for quotation in self:
                if quotation.project_ids:
                    for project in quotation.project_ids:
                        projects.append(project.id)
            if not projects:
                projecttemp = self.env['project.project'].search([('template', '=', True)], limit=1)
                values = {
                    'partner_id': copied_rec.partner_id.id,
                    'active': True,
                    'company_id': copied_rec.company_id.id,
                    'template': False,
                    'sale_order_id': copied_rec.id
                    }
                if projecttemp:
                    values['name'] = copied_rec.name 
                    project = projecttemp.copy(values)
                    project.tasks.write({
                        # 'sale_line_id': self.id,
                        'partner_id': copied_rec.partner_id.id,
                        'email_from': copied_rec.partner_id.email,
                    })
                    
                    # duplicating a project doesn't set the SO on sub-tasks
                #     project.tasks.filtered(lambda task: task.parent_id != False).write({
                #         'sale_line_id': self.id,
                #         'sale_order_id': self.order_id,
                #     })
                # else:
                    # project = self.env['project.project'].create(values)
                    copied_rec.project_id = project.id
                    projects.append(project.id)
                    copied_rec.project_ids = [(6, 0, projects)]
    
class Picking(models.Model):
    _inherit = 'stock.picking'
    
    project = fields.Boolean("Project")
        
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    unit = fields.Float("Unit")
    per_kw = fields.Float("Per KW")
    kw = fields.Float(related='order_id.kw', store=True)
    cost = fields.Float("Cost")
    total = fields.Float("Total")
    partner_ids = fields.Many2many('res.partner', 'vendor_template_rel1w', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_relw', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    hide = fields.Boolean("Hide")
    type = fields.Selection([('bom', 'BOM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC')], default='bom')
    name1 = fields.Char("Name")
    kwpunit = fields.Float("KWp Unit")
    printkwp = fields.Boolean("Print KWp Unit")
    quotation_template_line_id = fields.Many2one('sale.order.template.line', "Quotation Template")
    markup = fields.Float("Markup")
    
    
    @api.onchange('price_unit', 'markup')
    def onchange_price_unit_markup(self):
        if self.price_unit and self.markup:
            self.price_unit = self.price_unit + (self.price_unit * (self.markup /100))
        
class SaleOrderTemplate(models.Model):
    _name = 'sale.order.template'
    _inherit = [ 'sale.order.template', 'mail.thread', 'mail.activity.mixin']
    
    kw = fields.Float("KWP", copy=True)
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], default='draft', copy=False, track_visiblity='onchange')
    sale_order_id = fields.Many2one('sale.order', "Sale Order", track_visiblity='onchange')
    partner_id = fields.Many2one(related='sale_order_id.partner_id', store=True)
    opex_lines = fields.One2many('opex.lines', 'template_id', "OPEX", copy=True)
    opex_lines_site = fields.One2many('opex.lines.site', 'template_id', "OPEX Sites", copy=True)
    opex_lines_site_rate = fields.One2many('opex.lines.site.year', 'template_id', "OPEX", copy=True)
    opex_description = fields.Html("Summary", copy=True)
    subject = fields.Char("Subject", copy=True)
    reference = fields.Char("Reference", copy=True)
    kind_attn = fields.Char("Kind Attn.", copy=True)
    content = fields.Html("Content", default=default_content, copy=True)
    project_costing_id = fields.Many2one('product.entry', "Costing")
    costing_structure_ids = fields.One2many(related='project_costing_id.costing_structure_ids',)
    capex_opex = fields.Selection([('capex', 'Capex'), ('opex', 'Opex/ Open Access')], default='capex')
    type = fields.Selection([('sale', 'Sale'), ('project', 'Project')], default = 'sale')
    project_id = fields.Many2one('project.project', "Project")
    
    
    def approve(self):
        self.state = 'validated'
    
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
    cost = fields.Float("Kw Price")
    total = fields.Float("Total")
    partner_ids = fields.Many2many('res.partner', 'vendor_template_rel1', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_rel', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    hide = fields.Boolean("Hide")
    type = fields.Selection([('bom', 'BOM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC'),('project', 'Project')], default='bom')
    name1 = fields.Char("Name")
    kwpunit = fields.Float("KWp Unit")
    printkwp = fields.Boolean("Print KWp Unit")
    
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
    cost = fields.Float("Kw Price")
    total = fields.Float("Total")
    partner_ids = fields.Many2many('res.partner', 'vendor_template_rel2', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_rel22', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    hide = fields.Boolean("Hide")
    type = fields.Selection([('bom', 'BoM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC'),('project', 'Project')], default='bom')
    kwpunit = fields.Float("KWp Unit")
    printkwp = fields.Boolean("Print KWp Unit")
    
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
    sale_order_id = fields.Many2one('sale.order', "Sale Order", track_visiblity='onchange')
    
    
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
    sale_order_id = fields.Many2one('sale.order', "Sale Order", track_visiblity='onchange')
    
class OpexLinesSiteYear(models.Model):
    _name = 'opex.lines.site.year'
    _description = "Opex Lines Site Year"
    
    template_id = fields.Many2one('sale.order.template', "Template")
    site_id = fields.Many2one('opex.lines.site', "Site")
    particular = fields.Char("Particular")
    year = fields.Char("Tenure of Agreement")
    rate = fields.Float("Rate Rs. / Kwh")
    sale_order_id = fields.Many2one('sale.order', "Sale Order", track_visiblity='onchange')
