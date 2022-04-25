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

    # def unlink(self):
    #     for rec in self:
    #         line_id = self.env['sale.order.line'].search([('product_id.id', '=', rec.sale_order_line_id.product_id.id)])
    #         print("IDDDDDD",line_id)
    #         if not line_id:
    #             self.line_id
    #     return super(ProductEntry, self).unlink()
    def unlink(self):
        return super(ProductEntry, self).unlink()
    
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

    name = fields.Char('Name', default='New', copy=True , readonly = True)
    partner_id =  fields.Many2one('res.partner', related='sale_order_id.partner_id', string="Partner" )
    product_id =  fields.Many2one('product.product',copy=True,)
    product_uom_qty =  fields.Float(string='Quantity',related='sale_order_line_id.product_uom_qty',readonly = True)
    product_uom_id =  fields.Many2one('uom.uom', related='product_id.uom_id', readonly = True)
    total_material_cost = fields.Float(string='Total Material Cost', digits='Product Price', default=0.0, compute='all_material_cost', store=True, copy=True, readonly = True)
    agreed_price = fields.Float(string='Agreed Price')
    list_price = fields.Float(string='List Price')
    unit_price = fields.Float(string='Unit Price')
    net_realization = fields.Float(string='Net Realization',compute='_compute_cost')
    total_variable_cost = fields.Float(string='Total Variable Cost',compute='_compute_sum')
    subtotal_sum_a = fields.Float(string='Subtotal Sum A',compute='_compute_sum')
    # subtotal_sum_b = fields.Float(string='Subtotal Sum B',compute='_compute_sum')
    date = fields.Date("Date", default=lambda self: fields.Date.today())
    kw = fields.Integer("KWP")
    contribution_price = fields.Float(string='Contribution Price',compute='_get_price')
    contribution_percent = fields.Float(string='Contribution Percent',compute='_get_price')
    cost_per_wat = fields.Float("Cost / W", compute='compute_cost_per_wat', store=True)
    final_cost = fields.Float(string='Final Cost', digits='Product Price', default=0.0, compute='final_material_cost', copy=True)
    order_line = fields.One2many('product.entry.line', 'entry_id', copy=True, readonly = True)
    cost_lines = fields.One2many('product.entry.cost', 'entry_cost_id', copy=True, readonly = True)
    cost_lines_copy = fields.One2many('product.entry.cost.lines', 'cost_lines_id', copy=True, readonly = True)
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

    @api.onchange('quotation_template_id')
    def onchange_quotation_template_id(self):
        order_lines = [(5, 0, 0)]
        if self.quotation_template_id:
            for line in self.quotation_template_id.sale_order_template_line_ids:
                if line.product_id:
                    data = {
                        'product_uom_qty': line.product_uom_qty,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_uom_id.id,
                        'quotation_template_line_id' : line.id
                    }
                    order_lines.append((0, 0, data))

        self.order_line = order_lines
    
    
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


    @api.depends('agreed_price','subtotal_sum_a')
    def _compute_cost(self):
        net_cost = 0
        # variable_cost = 0
        for record in self:
            if record.agreed_price and record.subtotal_sum_a:
                net_cost = record.agreed_price - record.subtotal_sum_a
            # if record.agreed_price and record.subtotal_sum_b:
            #     variable_cost = record.agreed_price - record.subtotal_sum_b
            record.net_realization = net_cost
            # record.total_variable_cost = variable_cost


    @api.depends('cost_lines')
    def _compute_sum(self):
        sum_a = 0
        sum_b = 0
        for record in self:
            for line in record.cost_lines:
                sum_a += line.total
            record.subtotal_sum_a = sum_a
            for line in record.cost_lines_copy:
                sum_b += line.total
            record.total_variable_cost = sum_b


    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('product_entry') or '/'
        vals['name'] = name
        return super(ProductEntry, self).create(vals)




    def compute_amount(self):
        for entry in self.filtered(lambda x:x.sale_order_id):
            lines = entry.sale_order_id.mapped('order_line').filtered(lambda x:x.product_id == entry.product_id)
            if not lines:
                raise UserError(_('No such product find in order lines'))
            if not all(lines.filtered(lambda x: x.state == 'draft')):
                raise UserError(_('You can not update price of order in confirm state'))
            lines.write({'price_unit': entry.final_cost})
            entry.state = 'compute'

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
    
    @api.depends('product_uom_qty','cost')
    def compute_total(self):
        for rec in self:
            rec.total = rec.product_uom_qty * rec.cost

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

    # @api.depends('percentage','entry_cost_id.order_line')
    # def get_per_value(self):
    #     for line in self.filtered(lambda x:x.entry_cost_id):
    #         line.total = line.entry_cost_id.total_material_cost * line.percentage/100

    @api.onchange('percentage','cost_lines_id.order_line')
    def get_per_value(self):
        for line in self.filtered(lambda x:x.cost_lines_id):
            if line:
                line.total = line.cost_lines_id.total_material_cost * line.percentage/100

    name = fields.Char('List')
    percentage = fields.Float(string='Percentage', digits='Product Price', default=0.0, copy=True)
    # total = fields.Float(string='Subtotal', digits='Product Price', default=0.0, compute='get_per_value', copy=True)
    total = fields.Float(string='Subtotal', digits='Product Price', default=0.0, copy=True)
    cost_lines_id = fields.Many2one('product.entry', copy=True)
