# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

class ProductEntry(models.Model):
    _name = 'product.entry'
    _description = "Product Entry"
    
    @api.depends('cost_lines', 'order_line')
    def final_material_cost(self):
        for entry in self:
            entry.final_cost = entry.total_material_cost + sum(entry.mapped('cost_lines').mapped('total'))

    @api.depends('order_line')
    def all_material_cost(self):
        for entry in self:
            entry.total_material_cost = sum(entry.mapped('order_line').mapped('material_cost'))

    @api.depends('net_realization','total_variable_cost')
    def _get_price(self):
        percent = 0
        for rec in self:
            if rec.net_realization and rec.total_variable_cost:
                self.contribution_price = rec.net_realization - rec.total_variable_cost
                percent = (rec.net_realization - rec.total_variable_cost)/rec.net_realization
                self.contribution_percent = percent
            else:
                self.contribution_price = 0.00
                self.contribution_percent = 0.00

   
    
    @api.depends('order_line.total', 'order_line')
    def _compute_total(self):
        sum_a = 0.0
        for record in self:            
            for line in record.order_line:
                sum_a += line.total
            record.total = sum_a
            
    @api.depends('total', 'kw')
    def compute_cost_per_wat(self):
        for rec in self:
            if rec.kw > 0:
                rec.cost_per_wat = rec.total / (rec.kw * 1000) 
                
    @api.depends('quote_value', 'total')
    def _compute_quote(self):
        for record in self: 
            record.quote = record.quote_value * record.total
            
    @api.depends('quote', 'kw')
    def _compute_quote_per_watt(self):
        for record in self: 
            if record.kw > 0.0:
                record.quote_per_watt = record.quote / (record.kw * 1000)
            
    @api.depends('quote_per_watt', 'tax_value')
    def _compute_with_tax(self):
        for record in self: 
            record.with_tax = record.quote_per_watt * record.tax_value
            
    @api.depends('quote', 'total')
    def _compute_net_profit(self):
        for record in self: 
            record.net_profit = record.quote - record.total
            
    @api.depends('net_profit','quote', 'tax_value')
    def _compute_net_profit_percent(self):
        for record in self: 
            if (record.quote * record.tax_value) > 0.0:
                record.net_profit_percent = ((record.net_profit/(record.quote * record.tax_value)))*100
                
                
    @api.model
    def default_get(self,vals):
        templates = []
        vals = super(ProductEntry,self).default_get(vals)
        
        templates.append((0, 0,{'type': 'bom', 'cost': 0.0,'markup': 0.0, 'markup_amt': 0.0, 'quoted_price': 0.0, 'kw_price':0.0}))
        templates.append((0, 0,{'type': 'optional', 'cost': 0.0,'markup': 0.0, 'markup_amt': 0.0, 'quoted_price': 0.0, 'kw_price':0.0}))
        templates.append((0, 0,{'type': 'ic', 'cost': 0.0,'markup': 0.0, 'markup_amt': 0.0, 'quoted_price': 0.0, 'kw_price':0.0}))
        templates.append((0, 0,{'type': 'amc', 'cost': 0.0,'markup': 0.0, 'markup_amt': 0.0, 'quoted_price': 0.0, 'kw_price':0.0}))
        templates.append((0, 0,{'type': 'om', 'cost': 0.0,'markup': 0.0, 'markup_amt': 0.0, 'quoted_price': 0.0, 'kw_price':0.0}))
        templates.append((0, 0,{'type': 'camc', 'cost': 0.0,'markup': 0.0, 'markup_amt': 0.0, 'quoted_price': 0.0, 'kw_price':0.0}))
        vals.update({
            'costing_structure_ids': templates
        })
        return  vals
    
    
    name = fields.Char('Name', default='New', copy=True , readonly = True)
    partner_id =  fields.Many2one('res.partner', related='sale_order_id.partner_id', string="Partner" )
    product_id =  fields.Many2one('product.product',copy=True,)
    product_uom_qty =  fields.Float(string='Quantity',related='sale_order_line_id.product_uom_qty',readonly = True)
    product_uom_id =  fields.Many2one('uom.uom', related='product_id.uom_id', readonly = True)
    total_material_cost = fields.Float(string='Total Material Cost', digits='Product Price', default=0.0, compute='all_material_cost', store=True, copy=True, readonly = True)
    agreed_price = fields.Float(string='Agreed Price')
    list_price = fields.Float(string='List Price')
    unit_price = fields.Float(string='Unit Price')
    # subtotal_sum_b = fields.Float(string='Subtotal Sum B',compute='_compute_sum')
    date = fields.Date("Date", default=lambda self: fields.Date.today())
    kw = fields.Float("KWP")
    
    cost_per_wat = fields.Float("Cost / W", compute='compute_cost_per_wat', store=True)
    final_cost = fields.Float(string='Final Cost', digits='Product Price', default=0.0, compute='final_material_cost', copy=True)
    order_line = fields.One2many('product.entry.line', 'entry_id', copy=True, readonly = True)
    cost_lines = fields.One2many('product.entry.cost', 'entry_cost_id', copy=True, readonly = True)
    cost_lines_option = fields.One2many('product.entry.cost.lines', 'cost_lines_id', copy=True, readonly = True)
    total = fields.Float('Total', compute='_compute_total', store=True)
    sale_order_id = fields.Many2one('sale.order', copy=True)
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validated'), ('compute', 'Computed'),('cancel', 'Cancelled')], string='Status', readonly=True, copy=True, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    sale_order_line_id = fields.Many2one('sale.order.line', copy=True, track_visibility='always')
    quotation_template_id = fields.Many2one('sale.order.template', "Quotation Template")
    quote_value = fields.Float("Quote Value")
    tax_value = fields.Float("Tax Value")
    quote = fields.Float("Quote", compute='_compute_quote', store=True)
    quote_per_watt = fields.Float("Quote / W", compute='_compute_quote_per_watt', store=True)
    with_tax = fields.Float("w GST", compute='_compute_with_tax', store=True)
    net_profit = fields.Float("Net Profit", compute='_compute_net_profit', store=True)
    net_profit_percent = fields.Float("Net Profit %", compute='_compute_net_profit_percent', store=True)
    costing_structure_ids = fields.One2many('costing.structure', 'costing_id', "Costing", )
    

    @api.onchange('quotation_template_id')
    def onchange_quotation_template_id(self):
        order_lines = [(5, 0, 0)]
        option_lines = [(5, 0, 0)]
        if self.quotation_template_id:
            self.kw = self.quotation_template_id.kw
            for line in self.quotation_template_id.sale_order_template_line_ids:
                if line.product_id:
                    data = {
                        'product_uom_qty': line.product_uom_qty,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'quotation_template_line_id' : line.id,
                        'type': line.type,
                        'kwp': self.quotation_template_id.kw
                    }
                    order_lines.append((0, 0, data))
            for line in self.quotation_template_id.sale_order_template_option_ids:
                if line.product_id:
                    data = {
                        'product_uom_qty': line.quantity,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.uom_id.id,
                        'quotation_template_line_id' : line.id,
                        'kwp': self.quotation_template_id.kw
                    }
                    option_lines.append((0, 0, data))
        self.order_line = order_lines
        self.cost_lines_option = option_lines
    
    
    def action_validate(self):
        for order in self:
            # if order.quotation_template_id: 
            #     order.quotation_template_id.unlink()
            # template = self.env['sale.order.template'].create({'name': order.sale_order_id.name})
            for line in order.order_line:
                if line.quotation_template_line_id:
                    line.quotation_template_line_id.cost = line.cost
                    line.quotation_template_line_id.total = line.total
                    line.quotation_template_line_id.product_uom_qty = line.product_uom_qty
                if not line.quotation_template_line_id:
                    template_line = self.env['sale.order.template.line'].create({
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'product_uom_qty': line.product_uom_qty,
                        'product_uom_id': line.product_uom_id.id,
                        'cost': line.cost,
                        'total': line.total,
                        'sale_order_template_id': order.quotation_template_id.id
                        })
                    line.quotation_template_line_id = template_line.id
            if order.quotation_template_id:
                order.quotation_template_id.project_costing_id = self.id
                order.sale_order_id.project_costing_id = self.id
                    # template_line = self.env['sale.order.template.line'].create({
                    #     'sale_order_template_id': template.id,
                    #     'product_id': line.product_id.id,
                    #     'name': line.product_id.name,
                    #     'product_uom_qty': line.product_uom_qty,
                    #     'product_uom_id': line.product_uom_id.id,
                    #     'cost': line.cost,
                    #     'total': line.total
                    #     })
            order.quotation_template_id.state = 'validated'
            # template.state = 'validated'
            order.state = 'validate'

    def action_re_compute(self):
        for order in self:
            order.state = 'draft'

    def action_cancel(self):
        for order in self:
            order.state = 'cancel'

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('product_entry') or '/'
        vals['name'] = name
        return super(ProductEntry, self).create(vals)
    
    
class CostingStructure(models.Model):
    _name = 'costing.structure'
    _description = 'Costing Structure'
    
    @api.depends('costing_id.order_line', 'costing_id.order_line.type', 'costing_id.order_line.cost', 'costing_id.order_line.total', 'type', 'costing_id.cost_lines_option', 'costing_id.cost_lines_option.cost','costing_id.cost_lines_option.total')
    def compute_cost(self):
        for rec in self:
            bom_value = 0.0
            if rec.costing_id and rec.costing_id.order_line:
                if rec.type:
                    if rec.type == 'bom':
                        bom_total = rec.costing_id.order_line.filtered(lambda line: line.type == 'bom')
                        if bom_total:
                            bom_value = sum(l.total for l in bom_total)
                            rec.cost = bom_value
                        else:
                            rec.cost = 0.0
                    if rec.type == 'ic':
                        bom_total = rec.costing_id.order_line.filtered(lambda line: line.type == 'ic')
                        if bom_total:
                            bom_value = sum(l.total for l in bom_total)
                            rec.cost = bom_value
                        else:
                            rec.cost = 0.0
                    if rec.type == 'amc':
                        bom_total = rec.costing_id.order_line.filtered(lambda line: line.type == 'amc')
                        if bom_total:
                            bom_value = sum(l.total for l in bom_total)
                            rec.cost = bom_value
                        else:
                            rec.cost = 0.0
                    if rec.type == 'om':
                        bom_total = rec.costing_id.order_line.filtered(lambda line: line.type == 'om')
                        if bom_total:
                            bom_value = sum(l.total for l in bom_total)
                            rec.cost = bom_value
                        else:
                            rec.cost = 0.0
                    if rec.type == 'camc':
                        bom_total = rec.costing_id.order_line.filtered(lambda line: line.type == 'camc')
                        if bom_total:
                            bom_value = sum(l.total for l in bom_total)
                            rec.cost = bom_value
                        else:
                            rec.cost = 0.0
            if rec.costing_id and rec.costing_id.cost_lines_option:
                if rec.type == 'optional':
                    bom_total = rec.costing_id.cost_lines_option
                    if bom_total:
                        bom_value = sum(l.total for l in bom_total)
                        rec.cost = bom_value
                    else:
                        rec.cost = 0.0
                
                        
                    # if rec.type == 'ic':
                    #     bom_total = rec.costing_id.order_line.filtered(lambda line: line.type == 'ic')
                    #     if bom_total:
                    #         bom_value = sum(l.total for l in bom_total)
                    #         rec.cost = bom_value
                    #     else:
                    #         rec.cost = 0.0
    
    @api.depends('cost', 'markup')
    def compute_markup_amt(self):
        for rec in self:
            rec.markup_amt = rec.cost * (rec.markup / 100)
            
    @api.depends('cost', 'markup_amt')
    def compute_quoted_price(self):
        for rec in self:
            rec.quoted_price = rec.cost + rec.markup_amt
    
    @api.depends('quoted_price', 'costing_id.kw')        
    def compute_kw_price(self):
        for rec in self:
            if rec.costing_id.kw > 0:
                rec.kw_price = rec.quoted_price / rec.costing_id.kw
                
    @api.depends('quoted_price')        
    def compute_print_type(self):
        for rec in self:
            if rec.quoted_price > 0.0:
                rec.print_type = True
            else:
                rec.print_type = False
                
           
    cost = fields.Float("Cost", compute='compute_cost', store=True)
    markup = fields.Float("Markup %")
    markup_amt = fields.Float("Markup Amount", compute='compute_markup_amt', store=True)
    print_type = fields.Boolean('Print', compute='compute_print_type', store=True)
    quoted_price = fields.Float("Quoted Price", compute='compute_quoted_price', store=True)
    kw_price = fields.Float("Per Kwp Price", compute='compute_kw_price', store=True)
    costing_id = fields.Many2one('product.entry')
    type = fields.Selection([('bom', 'Main BOM'),('optional', 'Optional BOM'),
                             ('ic','Installation and Commissioning'),
                             ('amc', 'Annual Maintenance Charges'),
                             ('om', 'Operation and Maintenance'),
                             ('camc','Comprehensive Annual Maintenance Charges')], default='bom', string="Heading")
    

class ProductEntryLine(models.Model):
    _name = 'product.entry.line'
    _description = "Product Entry Line"

    @api.depends('price_unit', 'product_uom_qty', 'weight')
    def get_material_cost(self):
        for line in self:
            line.material_cost = line.price_unit * line.product_uom_qty * line.weight

    @api.onchange('product_id')
    def onchange_unit_cost(self):
        if self.product_id:
            self.weight = self.product_id.weight if self.product_id.weight else 1.0
            self.price_unit = self.product_id.standard_price if self.product_id.standard_price else 0.

    sequence = fields.Integer(string='Sequence', default=10, store=True, copy=True)
    entry_id = fields.Many2one('product.entry', store=True, copy=True)
    product_id = fields.Many2one('product.product', store=True, copy=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', default=1.0, store=True, copy=True)
    product_uom_id =  fields.Many2one('uom.uom', related='product_id.uom_id', store=True, copy=True)
    cost = fields.Float(string='Cost', store=True, copy=True)
    weight = fields.Float(digits='Product Unit of Measure', default=1.0, store=True, copy=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price', default=0.0, store=True, copy=True)
    material_cost = fields.Float(string='Material Cost', digits='Product Price', default=0.0, compute='get_material_cost', store=True, copy=True)
    remarks = fields.Char(string='Remarks', size=70, store=True, copy=True)
    total = fields.Float('Total', compute='compute_total')
    quotation_template_line_id = fields.Many2one('sale.order.template.line', "Quotation Template")
    kwp = fields.Float("KwP")
    kw_cost = fields.Float("Kw Cost")
    notes = fields.Char("Notes")
    type = fields.Selection([('bom', 'BoM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC')], default='bom')
    
    @api.depends('product_uom_qty','cost')
    def compute_total(self):
        for rec in self:
            rec.total = rec.product_uom_qty * rec.cost
            
    @api.onchange('kwp','kw_cost')
    def compute_cost(self):
        if self.kwp and self.kw_cost:
            self.cost = self.kwp * self.kw_cost

class ProductEntryCost(models.Model):
    _name = 'product.entry.cost'
    _description = "Product Entry Cost"

    # @api.depends('percentage','entry_cost_id.order_line')
    # def get_per_value(self):
    #     for line in self.filtered(lambda x:x.entry_cost_id):
    #         line.total = line.entry_cost_id.total_material_cost * line.percentage/100

    @api.onchange('percentage','entry_cost_id.order_line')
    def get_per_value(self):
        for line in self.filtered(lambda x:x.entry_cost_id):
            if line:
                line.total = line.entry_cost_id.total_material_cost * line.percentage/100

    name = fields.Char('List')
    percentage = fields.Float(string='Percentage', digits='Product Price', default=0.0, copy=True)
    # total = fields.Float(string='Subtotal', digits='Product Price', default=0.0, compute='get_per_value', copy=True)
    total = fields.Float(string='Subtotal', digits='Product Price', default=0.0, copy=True)
    entry_cost_id = fields.Many2one('product.entry', copy=True)


class ProductEntryCostLines(models.Model):
    _name = 'product.entry.cost.lines'
    _description = "Product Entry Cost Lines"

    sequence = fields.Integer(string='Sequence', default=10, store=True, copy=True)
    product_id = fields.Many2one('product.product', store=True, copy=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', default=1.0, store=True, copy=True)
    product_uom_id =  fields.Many2one('uom.uom', related='product_id.uom_id', store=True, copy=True)
    cost = fields.Float(string='Cost', store=True, copy=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price', default=0.0, store=True, copy=True)
    total = fields.Float('Total', compute='compute_total', store=True)
    quotation_template_line_id = fields.Many2one('sale.order.template.option', "Quotation Template")
    kwp = fields.Float("KwP")
    kw_cost = fields.Float("Kw Cost")
    notes = fields.Char("Notes")
    type = fields.Selection([('bom', 'BoM'),('ic','I&C'),('amc', 'AMC'),('om', 'O&M'),('camc','CAMC')], default='bom')
    cost_lines_id = fields.Many2one('product.entry', copy=True)
    
    @api.depends('product_uom_qty','cost')
    def compute_total(self):
        for rec in self:
            rec.total = rec.product_uom_qty * rec.cost
            
    @api.onchange('kwp','kw_cost')
    def compute_cost(self):
        if self.kwp and self.kw_cost:
            self.cost = self.kwp * self.kw_cost
