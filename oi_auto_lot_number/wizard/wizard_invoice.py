from odoo import _, fields, models


class MoveSerialNumber(models.TransientModel):
    _name = "move.serial.number.delivery"
    _description = "Move Serial Number"
    
    product_id = fields.Many2one('product.product', "Product")
    move_id = fields.Many2one('stock.move', "Move")
    lot_ids = fields.Many2many('stock.production.lot', 'lot_delivery_rel', 'del_id', 'lot_id', "Serial Numbers")
    
    def add_selected_lot(self):
        for line in self.lot_ids:
            sml = self.env['stock.move.line'].create({
                    'picking_id': self.move_id.picking_id.id,
                    'location_dest_id': self.move_id.location_dest_id.id,
                    'company_id': self.move_id.company_id.id,
                    'move_id': self.move_id.id,
                    'product_id': self.product_id.id,
                    'product_uom_id': self.move_id.product_uom.id,
                    'qty_done': 0,
                    'lot_id': line.id
                        })
        # view = self.env.ref('stock.view_stock_move_operations')
        # self = self.with_context(default_product_id=self.product_id.id,default_product_uom_qty=self.move_id.product_uom_qty,
        #                          default_product_uom = self.move_id.product_uom.id,
        #                          default_move_line_nosuggest_ids = self.move_id.move_line_nosuggest_ids.ids)
        # return {
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'stock.move',
        #     'views': [(view.id, 'form')],
        #     'target': 'new',
        #     'res_id': self.move_id.id,
        #     'context': self._context,
        # }
