from odoo import api, fields, models, _ 
from datetime import datetime
from odoo.exceptions import MissingError
from dateutil import parser,relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class GenerateClaimWarranty(models.TransientModel):
    _name = "generate.claim.warranty"
    _description = 'Generate Claim Warrantry'

    name = fields.Char(string='Name')
    date_of_claim = fields.Date(string='Date of Claim')
    expected_delivery_date = fields.Date(string="which date it  will be repaired?")    
    date_of_purchase = fields.Date(string='Purchase Date of Product')
    warranty_config_id = fields.Many2one('product.warranty.config',string='Warrantry Config')
    warranty_card_ids = fields.Many2many('warranty.card',string='Warranty Lines')
    claim_ids = fields.Many2many('claim.warranty',string='Claim Lines')

    
    def create_claim(self):
        claim=self.env['claim.warranty'].create({'warranty_card_id':self.env.context.get('id'),
                                            'date_of_claim':self.date_of_claim,
                                            'name':self.name})
        res= self.env.ref('product_warranty_cft.action_view_warranty_claim_cft').read()[0]
        res.update({'views':[(self.env.ref('product_warranty_cft.view_warranty_claim_cft_form').id,'form')],
                    'res_id':claim.id})
        return res

    
    def create_mass_claim(self):
        warning_list=[]
        wrning_lst=[]
        claim_ids = []
        claim_obj = self.env['claim.warranty']
        warranty_config_obj = self.env['product.warranty.config']
        for wrt in self.warranty_card_ids:
            warranty_config = wrt.product_id.warranty_config_id or wrt.product_id.product_tmpl_id.warranty_config_id or wrt.product_id.categ_id.warranty_config_id
            if not warranty_config:
                warranty_config = warranty_config_obj.search([('applied_on','=','3_global')],order='sequence',limit=1)
                if not warranty_config:
                    warning_list.append(wrt.product_id.name or wrt.name+"'s product")
                    continue
            if warranty_config and not warranty_config.claim_sequence_id:
                wrning_lst.append(warranty_config.name)
                continue
            claim=claim_obj.create({'warranty_card_id':wrt.id,
                                    'name':warranty_config.claim_sequence_id.next_by_id(),
                                    'date_of_claim':self.date_of_claim,
                                    'expected_delivery_date':self.expected_delivery_date
                                    })
            claim_ids.append(claim.id)

        self.write({'claim_ids':[(6,0,claim_ids)]})
        if warning_list or wrning_lst:
            warrning = ''
            if warning_list:
                warrning += 'Please Set Warranty configuration in %s'%(', ' .join(set(warning_list)))
            if wrning_lst:
                warrning +=' Please Set Claim Sequence in %s'%(', '.join(set(wrning_lst)))

            raise UserError(_(warrning))
        return True

    
    def view_claim_records(self):
        claim_lines=[]
        for claim_line in self.claim_ids:
            claim_lines.append(claim_line.id)
        if claim_lines:
            action = self.env.ref('product_warranty_cft.action_view_warranty_claim_cft').read()[0]
            if len(claim_lines) > 1:
                action['domain'] = [('id', 'in', claim_lines)]
            elif claim_lines:
                action['views'] = [(self.env.ref('product_warranty_cft.view_warranty_claim_cft_form').id, 'form')]
                action['res_id'] = claim_lines[0]
            return action
        else:
            raise exceptions.Warning('There is no Claim line')


    @api.model
    def default_get(self,default_fields):
        res = super(GenerateClaimWarranty, self).default_get(default_fields)
        if self._context.get('mass_claim'):
            return res
        warranty_card = self.env['warranty.card'].browse(self.env.context.get('id'))
        product = warranty_card.product_id
        warranty_config = product.warranty_config_id or product.product_tmpl_id.warranty_config_id or product.categ_id.warranty_config_id
        if not warranty_config:
            warranty_config = self.env['product.warranty.config'].search([('applied_on','=','3_global')],order='sequence',limit=1)
        if not warranty_config:
            raise UserError('Please Create Warrantry Configuration of product "%s"'%product.name)
        if not warranty_config.claim_sequence_id:
            raise UserError('Please Set Claim Sequence in %s'%warranty_config.name)
        name = warranty_config and warranty_config.claim_sequence_id and warranty_config.claim_sequence_id.next_by_id() #or warranty_card.name+'_'
        res.update({'name':name,'warranty_config_id':warranty_config and warranty_config.id or False})
        return res