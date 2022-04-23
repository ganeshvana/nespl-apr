from odoo import models, fields, api
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    lot_number = fields.Char("Lot Count")
    done_to_update = fields.Float("Done Qty")
    secondary_done_to_update = fields.Float("Secondary Done Qty")
    from_lot = fields.Char("From Lot", copy=False)
    to_lot = fields.Char("To Lot", copy=False)
    
    def get_serial_number(self):
        view = self.env.ref('oi_auto_lot_number.move_serial_number_delivery_form')
        self = self.with_context(default_product_id=self.product_id.id,default_move_id=self.id)
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'move.serial.number.delivery',
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': self._context,
        }
    
    def create_lot(self):
        next_seq = self.product_id.lot_sequence_number_next
        final_seq = next_seq + int(self.lot_number)
        x = range(int(next_seq), int(final_seq))
        if self.picking_id.state not in ['done', 'cancel']:
            for loop in x:
                if self.product_id.lot_sequence_id:
                    last_lot = self.product_id.lot_sequence_id._next()
                else:
                    last_lot = self.env['ir.sequence'].next_by_code('move.lot.seq2')
                lot = self.env['stock.production.lot'].create({'name': last_lot, 'product_id': self.product_id.id})
                sml = self.env['stock.move.line'].create({
                    'picking_id': self.picking_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'company_id': self.company_id.id,
                    'move_id': self.id,
                    'product_id': self.product_id.id,
                    'picking_id': self.picking_id.id,
                    'product_uom_id': self.product_uom.id,
                    'qty_done': 1,
                    'lot_id': lot.id
                        })
        view = self.env.ref('stock.view_stock_move_operations')
        self = self.with_context(default_product_id=self.product_id.id,default_product_uom_qty=self.product_uom_qty,
                                 default_product_uom = self.product_uom.id,
                                 default_reserved_availability = self.reserved_availability,
                                 default_move_line_nosuggest_ids = self.move_line_nosuggest_ids.ids)
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': self._context,
        }
    
    def remove_lines(self):
        if self.picking_id.state not in ['done', 'cancel']:
            
            if self.move_line_ids:
                for loop in self.move_line_ids:
                    if loop.select == True:
                        loop.unlink()    
                        self._cr.commit()
                
        view = self.env.ref('stock.view_stock_move_operations')
        self = self.with_context(default_product_id=self.product_id.id,default_product_uom_qty=self.product_uom_qty,
                                 default_product_uom = self.product_uom.id,
                                 default_reserved_availability = self.reserved_availability,
                                 default_move_line_nosuggest_ids = self.move_line_nosuggest_ids.ids)
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': self._context,
        }
        
    def create_lots(self):    
#         if not self.lot_sequence:
#             raise UserError("Click on Get Lot to get Lot Sequence.")
        if self.lot_sequence:
            x = range(int(self.from_lot), int(self.to_lot + 1))
            if self.picking_id.state not in ['done', 'cancel']:
                for loop in x:                
                    last_lot = str(self.lot_sequence) + '000' + str(loop)
                    lot = self.env['stock.production.lot'].create({'name': last_lot, 'product_id': self.product_id.id})
                    sml = self.env['stock.move.line'].create({
                        'picking_id': self.picking_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'company_id': self.company_id.id,
                        'move_id': self.id,
                        'product_id': self.product_id.id,
                        'picking_id': self.picking_id.id,
                        'product_uom_id': self.product_uom.id,
                        'qty_done': 1,
                        'lot_id': lot.id
                            })
        if not self.lot_sequence:
            x = range(int(self.from_lot), int(self.to_lot + 1))
            if self.picking_id.state not in ['done', 'cancel']:
                for loop in x:                
                    last_lot = self.env['ir.sequence'].next_by_code('move.lot.manual.seq')
                    lot = self.env['stock.production.lot'].create({'name': last_lot, 'product_id': self.product_id.id})
                    sml = self.env['stock.move.line'].create({
                        'picking_id': self.picking_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'company_id': self.company_id.id,
                        'move_id': self.id,
                        'product_id': self.product_id.id,
                        'picking_id': self.picking_id.id,
                        'product_uom_id': self.product_uom.id,
                        'qty_done': 1,
                        'lot_id': lot.id
                            })
        view = self.env.ref('stock.view_stock_move_operations')
        self = self.with_context(default_product_id=self.product_id.id,default_product_uom_qty=self.product_uom_qty,
                                 default_product_uom = self.product_uom.id,
                                 default_reserved_availability = self.reserved_availability,
                                 default_move_line_nosuggest_ids = self.move_line_nosuggest_ids.ids)
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': self._context,
        }
        
    def done_qty_update(self):        
        if self.picking_id.state not in ['done', 'cancel']:
            if self.move_line_nosuggest_ids:
                for loop in self.move_line_nosuggest_ids:
                    if loop.select == True:
                        loop.qty_done = self.done_to_update
                        loop.secondary_done_qty = self.secondary_done_to_update   
                for loop in self.move_line_nosuggest_ids:
                    loop.select = False   
                self.done_to_update = 0.0
                self.secondary_done_to_update = 0.0
            if self.move_line_ids:
                for loop in self.move_line_ids:
                    if loop.select == True:
                        loop.qty_done = self.done_to_update
                        loop.secondary_done_qty = self.secondary_done_to_update       
                for loop in self.move_line_ids:
                    loop.select = False    
                self.done_to_update = 0.0
                self.secondary_done_to_update = 0.0
        view = self.env.ref('stock.view_stock_move_operations')
        self = self.with_context(default_product_id=self.product_id.id,default_product_uom_qty=self.product_uom_qty,
                                 default_product_uom = self.product_uom.id,
                                 default_reserved_availability = self.reserved_availability,
                                 default_move_line_nosuggest_ids = self.move_line_nosuggest_ids.ids,
                                 default_move_line_ids = self.move_line_ids.ids)
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': self._context,
        }
        
     
        
class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    select = fields.Boolean("Select", default=True)
    
class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'    
    
    qty = fields.Float("Qty", compute='compute_qty', store=True)
    
    @api.depends('product_qty')
    def compute_qty(self):
        for rec in self:
            rec.qty = rec.product_qty
    
    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.name = self.env['ir.sequence'].next_by_code('move.lot.manual.seq')   
            
    
class StockMove(models.Model):
    _inherit = 'stock.move'
    
    lot_sequence = fields.Char("Lot Sequence", copy=False)
    from_lot = fields.Integer("From Lot", copy=False)
    to_lot = fields.Integer("To Lot", copy=False)
    
    def get_lot(self):
        if self.picking_id:
            if self.picking_id.move_ids_without_package:
               
#                 no_lot_sequence = all(line.lot_sequence == 0 for line in self.picking_id.move_ids_without_package)
#                 if no_lot_sequence:
#                     self.lot_sequence = 1
#                 if not no_lot_sequence:
#                     sorted_lines = self.picking_id.move_ids_without_package.sorted(lambda m: m.lot_sequence, reverse=True)
#                     print(sorted_lines, "sorted_lines----") 
#                     seq = sorted_lines[0].lot_sequence
#                     self.lot_sequence = seq + 1
                self.lot_sequence = self.env['ir.sequence'].next_by_code('move.lot.seq')
    
    
