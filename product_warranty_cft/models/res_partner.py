from odoo import api, exceptions, fields, models, _

class ResPartner(models.Model):

    _inherit = "res.partner"

    warranty_card_ids = fields.One2many('warranty.card','partner_id',string="Warranty Cards")
    warranty_cards_count = fields.Integer(compute="_get_warranty_count")

    
    def _get_warranty_count(self):
        for record in self:
            record.warranty_cards_count = len(record.warranty_card_ids)