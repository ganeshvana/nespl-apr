from odoo import api, exceptions, fields, models, _
from datetime import datetime
from dateutil import parser,relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class WarrantyWizard(models.TransientModel):
    _name = "warranty.wizard"
    _description = "Warranty Wizard"

    create_warranty_from = fields.Selection([('delivery_date','Delivered Date'),('now','Current Date'),('other','Manually Enter')],string="Create Warranty From ?")
    validity_from = fields.Date(string='Validity From')
    validity_to = fields.Date(string='Validity To')
    name = fields.Char(string='Name')
    date_of_purchase = fields.Date(string='Purchase Date of Product')
    warranty_config_id = fields.Many2one('product.warranty.config',string='Warranty Config')

    picking_type_code = fields.Selection([
        ('incoming', 'Purchase'),
        ('outgoing', 'Sales')],string="Create warranty of sales or purchase")
    stock_move_ids = fields.Many2many('stock.move',string='Delivery Lines')
    warranty_card_ids = fields.Many2many('warranty.card',string='Warranty Lines')

    
    def create_warranty(self):
        stock_move_id=self.env.context.get('id')
        card=self.env['warranty.card'].create({'validity_from':self.validity_from,
                                            'validity_to':self.validity_to,
                                            'stock_move_id':stock_move_id,
                                            'user_id':self._uid,
                                            'purchase_date':self.date_of_purchase,
                                            'name':self.name})
        res= self.env.ref('product_warranty_cft.action_view_warranty_card_cft').read()[0]
        res.update({'views':[(self.env.ref('product_warranty_cft.view_warranty_card_cft_form').id,'form')],
                    'res_id':card.id})
        return res

    
    def create_mass_warranty(self):
        warranty_card_obj = self.env['warranty.card']
        warranty_config_obj = self.env['product.warranty.config']
        warning_list=[]
        card_ids=[]
        for move in self.stock_move_ids:
            product = move.product_id
            validity_to = self.validity_to
            warranty_config = product.warranty_config_id or product.product_tmpl_id.warranty_config_id or product.categ_id.warranty_config_id
            if not warranty_config:
                warranty_config = warranty_config_obj.search([('applied_on','=','3_global')],order='sequence',limit=1)
            if not warranty_config:
                warning_list.append(product.name)
                continue
            name = warranty_config and warranty_config.warranty_sequence_id and warranty_config.warranty_sequence_id.next_by_id() or (move.sale_line_id or move.purchase_line_id and product.name +'_'+ move.sale_line_id.order_id.name or move.purchase_line_id.order_id.name) or move.name
             
            if self.create_warranty_from =='delivery_date':
                validity_from = move.create_date
            else:
                validity_from = self.validity_from

            if warranty_config and self.create_warranty_from =='delivery_date':
                if warranty_config.warranty_unit=='years':
                    validity_to = parser.parse(str(validity_from)) + relativedelta.relativedelta(years=warranty_config.warranty_period)
                elif warranty_config.warranty_unit == 'months':
                    validity_to = parser.parse(str(validity_from)) + relativedelta.relativedelta(months=warranty_config.warranty_period)
                else:
                    validity_to = parser.parse(str(validity_from)) + relativedelta.relativedelta(days=warranty_config.warranty_period)
            if not validity_to and self.create_warranty_from == 'delivery_date':
                warning_list.append(product.name)
                continue
            
            card_id = warranty_card_obj.create({
                'validity_from':str(validity_from),'validity_to':str(validity_to),
                'stock_move_id':move.id,'user_id':self._uid,'name':name})
            card_ids.append(card_id.id)

        self.write({'warranty_card_ids': [(6,0,card_ids)]})
        if warning_list:
            raise exceptions.UserError('Please Set Warranty configuration in %s'%(', ' .join(warning_list)))
        return True
    
    def view_warranty_records(self):
        warranty_lines=[]
        for warranty_line in self.warranty_card_ids:
            warranty_lines.append(warranty_line.id)
        if warranty_lines:
            action = self.env.ref('product_warranty_cft.action_view_warranty_card_cft').read()[0]
            if len(warranty_lines) > 1:
                action['domain'] = [('id', 'in', warranty_lines)]
            elif warranty_lines:
                action['views'] = [(self.env.ref('product_warranty_cft.view_warranty_card_cft_form').id, 'form')]
                action['res_id'] = warranty_lines[0]
            return action
        else:
            raise exceptions.UserError('There is no warranty line')

  
    
    @api.onchange('create_warranty_from')
    def onchange_create_warranty_from(self):
        # if self.create_warranty_from == 'other':
        #     return
        if self.create_warranty_from == 'now':
            self.validity_from = str(datetime.now())
        if self.create_warranty_from =='delivery_date' and self.env.context.get('id') :
            self.validity_from = str(self.env['stock.move'].browse(self.env.context.get('id')).create_date)
        return

    
    @api.onchange('validity_from')
    def onchange_validity_from(self):
        if self.warranty_config_id and self.validity_from:
            if self.warranty_config_id.warranty_unit=='years':
                self.validity_to = str(parser.parse(str(self.validity_from)) + relativedelta.relativedelta(years=self.warranty_config_id.warranty_period))
            elif self.warranty_config_id.warranty_unit == 'months':
                self.validity_to = str(parser.parse(str(self.validity_from)) + relativedelta.relativedelta(months=self.warranty_config_id.warranty_period))
            else:
                self.validity_to = str(parser.parse(str(self.validity_from)) + relativedelta.relativedelta(days=self.warranty_config_id.warranty_period))
        return

    @api.model
    def default_get(self,default_fields):
        res= super(WarrantyWizard,self).default_get(default_fields)
        if self._context.get('mass_warrantry_from_picking'):
            picking= self.env['stock.picking'].browse(self._context.get('picking_id'))
            move_lines= picking.move_lines
            res.update({'stock_move_ids':[(6,0,move_lines.ids)]})
            return res

        if self._context.get('mass_warrantry'):
            return res
        if self.env.context.get('id'):
            res={}
            stock_move_rec = self.env['stock.move'].browse(self.env.context.get('id'))
            product = stock_move_rec.product_id
            warranty_config = product.warranty_config_id or product.product_tmpl_id.warranty_config_id or product.categ_id.warranty_config_id
            if not warranty_config:
                warranty_config = self.env['product.warranty.config'].search([('applied_on','=','3_global')],order='sequence',limit=1)
            name = warranty_config and warranty_config.warranty_sequence_id and warranty_config.warranty_sequence_id.next_by_id() or  stock_move_rec.sale_line_id or stock_move_rec.purchase_line_id and '%s_%s'%(product.name,stock_move_rec.sale_line_id.order_id.name or stock_move_rec.purchase_line_id.order_id.name) or stock_move_rec.name
            res.update({'name':name,'warranty_config_id':warranty_config and warranty_config.id or False})
        return res