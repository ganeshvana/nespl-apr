from odoo import api, fields, models, tools, _
from odoo.tools.misc import formatLang, get_lang


class TDSMaster(models.Model):
    _name = "tds.master"

    type = fields.Selection([('goods_tds', 'Goods TDS'), ('service_tds', 'Service TDS')], "Type", default='tds')
    max_amount = fields.Float("Maximum Amount")
    tax_id = fields.Many2one('account.tax', "Tax")
    fiscal_year_id = fields.Many2one('account.fiscalyear', "Fiscal Year")