# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.tools import is_html_empty


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    entry_count = fields.Integer(string='Entry Count', compute='count_entry')
    
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

    

    # @api.model
    # def create(self, vals):
    #     # Entry = self.env['product.entry']
    #     res = super(SaleOrder, self).create(vals)
    #     if len(res.order_line) > 0:
    #         for line in res.order_line:
    #             var = self.env['product.entry'].create({'partner_id': res.partner_id.id,'sale_order_id': res.id, 'sale_order_line_id': line.id, 'product_id': line.product_id.id,'product_uom_id': line.product_uom,'list_price':line.price_subtotal,'unit_price':line.price_unit})  
    #     return res
    
    # def write(self,vals):
    #     res = super(SaleOrder, self).write(vals)
    #     if len(self.order_line) > 0:
    #         for line in self.order_line:
    #             entry = self.env['product.entry'].search([('sale_order_line_id.product_id.id', '=', line.product_id.id),('sale_order_id', '=' , self.id)])
    #             product_entry = self.env['product.entry'].search([('sale_order_line_id', '=' , False)]).unlink()
    #             print("Entry",product_entry)
    #
    #             if not entry:
    #                 var = self.env['product.entry'].create({'partner_id': self.partner_id.id, 'sale_order_line_id': line.id, 'sale_order_id': self.id, 'product_id': line.product_id.id,'product_uom_id': line.product_uom})
    #
    #     return res

    def unlink(self):
        return super(SaleOrder, self).unlink()

    # def unlink(self):
    #     for rec in self:
    #         line_id = self.env['product.entry'].search([('sale_order_line_id.product_id.id', '=', line.product_id.id),('sale_order_id', '=' , self.id)])
    #         print("IDDDDDD",self.id)
    #         if not line_id:
    #             self.line_id.unlink()
    #     return super(SaleOrder, self).unlink()

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
    
    kw = fields.Integer("KWP")
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated')], default='draft')

class SaleOrderTemplateLine(models.Model):
    _inherit = 'sale.order.template.line'
    
    unit = fields.Float("Unit")
    per_kw = fields.Float("Per KW", compute='compute_per_kw', store=True)
    kw = fields.Integer(related='sale_order_template_id.kw', store=True)
    cost = fields.Float("Cost")
    total = fields.Float("Total")
    
    @api.depends('kw', 'unit')
    def compute_per_kw(self):
        for rec in self:
            if rec.unit > 0.0:
                rec.per_kw = (rec.kw * 1000)/rec.unit
