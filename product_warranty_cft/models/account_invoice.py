from odoo import api,fields, models

class AccountInvoice(models.Model):

    _inherit = 'account.move'

    claim_id = fields.Many2one('claim.warranty',string='Warranty Claim')
