# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'product template'
    
    alternative_products_ids = fields.Many2many("product.product", 'prod_template_alter_rel', 'name',
                                                'barcode', string="Alternative Products")

                                               
class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = 'product product'
    
    @api.model
    @api.returns('self',
        upgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else self.browse(value),
        downgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else value.ids)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if 'add_domain' in self._context and self._context['add_domain']:
            args+= [('product_tmpl_id', '!=', self._context['add_domain'])]
        return super(ProductProduct, self).search(args, offset, limit, order, count)
    
class ProductsWizard(models.TransientModel):
    _name = 'products.wizard'
    _description = "Products wizard"
    
    alternatives_id = fields.Many2one('product.product', string="Alternative" )
    product_ids = fields.Many2many("product.product",  string="Alternative Products", readonly=1)

    @api.model
    def default_get(self, fields):
        res1 = super(ProductsWizard, self).default_get(fields)
        rat = self.env['sale.order.line'].browse(self._context.get('active_id', []))
        prod_ids = []
        if rat.product_id and rat.product_id.alternative_products_ids:
            prod_ids = rat.product_id.alternative_products_ids.mapped('id')
        res1['product_ids'] = [(6, 0, prod_ids)]
        return res1
    
    def replace(self):
        rat_obj = self.env['sale.order.line']
        rat_active = rat_obj.browse(self._context.get('active_id', []))
        new_prod_id = self.alternatives_id.id
        rat_active.product_id = new_prod_id
        res = rat_active.product_id_change()
        return res
