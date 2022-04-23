from odoo import fields, models,api

class ProductWarrantyConfig(models.Model):
    _name='product.warranty.config'
    _description = 'Product Warranty Config'


    name = fields.Char('Name',  translate=True)
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the pricelist without removing it.")
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='3_global',help='Warranty applicable on selected option')

    
    def domain_warranty_sequence_id(self):
        warranty_seq = self.env['ir.sequence'].search([('name','ilike','Warranty')])
        return [('id','in',warranty_seq.ids)]

    
    def domain_warranty_claim_sequence_id(self):
        claim = self.env['ir.sequence'].search([('name','ilike','Claim')])
        return [('id','in',claim.ids)]


    company_id = fields.Many2one('res.company', 'Company')
    sequence = fields.Integer(default=16)
    warranty_period = fields.Integer("Select Warranty Period")
    warranty_unit = fields.Selection([('days','Days'),('months','Month'),('years','Year')])
    warranty_sequence_id = fields.Many2one('ir.sequence',string='Set Warranty Sequence',domain=domain_warranty_sequence_id)
    claim_sequence_id = fields.Many2one('ir.sequence',string='Claim Sequence',domain=domain_warranty_claim_sequence_id)
    product_tmpl_ids = fields.One2many(
        'product.template','warranty_config_id', 'Product Template', ondelete='cascade',
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    product_ids = fields.One2many(
        'product.product','warranty_config_id', 'Product', ondelete='cascade',
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.")
    categ_ids = fields.One2many(
        'product.category','warranty_config_id', 'Product Category', ondelete='cascade',
        help="Specify a product category if this rule only applies to products belonging to this category or its children categories. Keep empty otherwise.")

    @api.model
    def create(self,vals):
        try:
            sequence=self.env.ref('product_warranty_cft.sequence_of_warranty_configuration')
            if sequence:
                name=sequence.next_by_id()
            else:
                name='/'
        except:
            name='/'
        vals.update({'name':name})
        res  = super(ProductWarrantyConfig, self).create(vals)
        return res

class IrSequence(models.Model):
    _inherit='ir.sequence'

    @api.model
    def default_get(self,default_fields):
        res=super(IrSequence, self).default_get(default_fields)
        if self.env.context.get('warranty_seq'):
            res.update({'name':'Warranty_'})
        if self.env.context.get('claim_seq'):
            res.update({'name':'Claim_'})
        return res