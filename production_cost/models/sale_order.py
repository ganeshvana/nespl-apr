# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    entry_count = fields.Integer(string='Entry Count', compute='count_entry')
    

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
