from odoo import api, fields, models, tools, _
from odoo.tools.misc import formatLang, get_lang
from datetime import datetime, timedelta


class res_partner(models.Model):
    _inherit = "res.partner"

    total_billed = fields.Monetary(compute='_invoice_total_billed', string="Total Billed",
        groups='account.group_account_invoice,account.group_account_readonly')
    goods_tds_applicable = fields.Boolean(string="Goods TDS Applicable", default=False,)
    service_tds_applicable = fields.Boolean(string="Contract TDS Applicable", default=False,)


    @api.depends('total_billed')
    def _compute_tds_eligible(self):
        for record in self:
            record.is_tds_eligible = ''
            if record.total_billed < -5000000:
                record.is_tds_eligible = True
            else:
                record.is_tds_eligible = False



    def _invoice_total_billed(self):
        self.total_billed = 0
        if not self.ids:
            return True
        todays_date = fields.Date.today()
        year = todays_date.year
        fdate = '01-04-'+str(year) + ' 00:00:00'
        from_date =  datetime.strptime(fdate, '%d-%m-%Y %H:%M:%S')
        tdate = '31-03-'+ str(year+1) + ' 00:00:00'
        to_date =  datetime.strptime(tdate, '%d-%m-%Y %H:%M:%S')
        all_partners_and_children = {}
        all_partner_ids = []
        for partner in self.filtered('id'):
            # price_total is in the company currency
            all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
            all_partner_ids += all_partners_and_children[partner]

        domain = [
            ('partner_id', 'in', all_partner_ids),
            ('state', 'not in', ['draft', 'cancel']),
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('invoice_date', '>=', from_date), 
            ('invoice_date', '<=', todays_date),
        ]
        price_totals = self.env['account.invoice.report'].read_group(domain, ['price_subtotal'], ['partner_id'])
        for partner, child_ids in all_partners_and_children.items():
            partner.total_billed = sum(price['price_subtotal'] for price in price_totals if price['partner_id'][0] in child_ids)


    def action_view_partner_bills(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        action['domain'] = [
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('partner_id', 'child_of', self.id),
        ]
        action['context'] = {'default_move_type':'in_invoice', 'move_type':'in_invoice', 'journal_type': 'purchase', 'search_default_unpaid': 1}
        return action
    

# class purchase_order_line(models.Model):
#     _inherit = "purchase.order.line"

    # def _product_id_change(self):
    #     if not self.product_id:
    #         return
    #
    #     self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
    #     product_lang = self.product_id.with_context(
    #         lang=get_lang(self.env, self.partner_id.lang).code,
    #         partner_id=self.partner_id.id,
    #         company_id=self.company_id.id,
    #     )
    #     self.name = self._get_product_purchase_description(product_lang)
    #     if not self.order_id.partner_id.is_tds_eligible:
    #         self._compute_tax_id()
    #     else:
    #         self.taxes_id= [(6,0,[93])]


class account_move(models.Model):
    _inherit = 'account.move'
    
    service_tds_applicable = fields.Boolean("TDS Applicable")
    tds_applied = fields.Boolean("TDS Applied")
    
    @api.onchange('partner_id')
    def onchange_partner(self):
        todays_date = date.today()
        year = todays_date.year
        fdate = '01-04-'+str(year)
        from_date =  datetime.strptime(fdate, '%d-%m-%YYYY')
        tdate = '31-03-'+ str(year+1)
        to_date =  datetime.strptime(tdate, '%d-%m-%YYYY')
        if self.partner_id and self.move_type == 'in_invoice' and self.partner_id.service_tds_applicable:
            if self.amount_total > 30000:
                self.service_tds_applicable = True
            else:                
                bills = self.env['account.move'].search([('partner_id', '=', self.partner_id.id), ('move_type', '=', 'in_invoice'),
                                                     ('invoice_date' '>=', from_date), ('invoice_date', '<=', todays_date),
                                                     ('state', '=', 'posted')])
                if bills:
                    bills_total = sum(l.amount_untaxed_signed for l in bills)
                    tds_master = self.env['tds.master'].search([('max_amount', '<', bills_total), ('type', '=', 'service_tds')])
                    if tds_master:
                        self.service_tds_applicable = True

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            line.name = line._get_computed_name()
            line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(taxes)
            if not self.move_id.partner_id.goods_tds_applicable:
                line.tax_ids = taxes
            else:
                line.tax_ids = [(6,0,[93])]
                tds_master = self.env['tds.master'].search([('type', '=', 'goods_tds')])
                if tds_master:
                    tax = tds_master.tax_id.id
                    line.tax_ids = [(6,0,[tax])]
            line.product_uom_id = line._get_computed_uom()
            line.price_unit = line._get_computed_price_unit()



    def _get_computed_taxes(self):
        self.ensure_one()
        if not self.move_id.partner_id.goods_tds_applicable:
            if self.move_id.is_sale_document(include_receipts=True):
                # Out invoice.
                if self.product_id.taxes_id:
                    tax_ids = self.product_id.taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
                elif self.account_id.tax_ids:
                    tax_ids = self.account_id.tax_ids
                else:
                    tax_ids = self.env['account.tax']
                if not tax_ids and not self.exclude_from_invoice_tab:
                    tax_ids = self.move_id.company_id.account_sale_tax_id
            elif self.move_id.is_purchase_document(include_receipts=True):
                # In invoice.
                if self.product_id.supplier_taxes_id:
                    tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.move_id.company_id)
                elif self.account_id.tax_ids:
                    tax_ids = self.account_id.tax_ids
                else:
                    tax_ids = self.env['account.tax']
                if not tax_ids and not self.exclude_from_invoice_tab:
                    tax_ids = self.move_id.company_id.account_purchase_tax_id
            else:
                # Miscellaneous operation.
                tax_ids = self.account_id.tax_ids

            if self.company_id and tax_ids:
                tax_ids = tax_ids.filtered(lambda tax: tax.company_id == self.company_id)

        if self.move_id.partner_id.goods_tds_applicable:
            tds_master = self.env['tds.master'].search([('type', '=', 'goods_tds')])
            if tds_master:
                
                tax = tds_master.tax_id.id
                tax_ids = [(6,0,[tax])]
                
        if self.move_id.partner_id.service_tds_applicable:
            tds_master = self.env['tds.master'].search([('type', '=', 'service_tds')])
            if tds_master:
                tax = tds_master.tax_id.id
                tax_ids = [(6,0,[tax])]

        return tax_ids