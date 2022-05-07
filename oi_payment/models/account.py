from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class Move(models.Model):
    _inherit = "account.move"
    
    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref(self._get_mail_template(), raise_if_not_found=False)
        lang = False
        if template:
            lang = template._render_lang(self.ids)[self.id]
        if not lang:
            lang = get_lang(self.env).code
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'account.move',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template),
            'default_template_id': template.id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            'custom_layout': "mail.mail_notification_paynow",
            'force_email': True,
            'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
        # compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
        # ctx = dict(
        #     default_model='account.move',
        #     default_res_id=self.id,
        #     # For the sake of consistency we need a default_res_model if
        #     # default_res_id is set. Not renaming default_model as it can
        #     # create many side-effects.
        #     default_res_model='account.move',
        #     default_use_template=bool(template),
        #     default_template_id=template and template.id or False,
        #     default_composition_mode='comment',
        #     mark_invoice_as_sent=True,
        #     custom_layout="mail.mail_notification_paynow",
        #     model_description=self.with_context(lang=lang).type_name,
        #     force_email=True,
        #     wizard_opened=True
        # )
        # return {
        #     'name': _('Send Invoice'),
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'account.invoice.send',
        #     'views': [(compose_form.id, 'form')],
        #     'view_id': compose_form.id,
        #     'target': 'new',
        #     'context': ctx,
        # }
    
    def action_register_payment(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        pricelist_lines = []
        sale_id = False
        purchase_id = False
        milestone = []
        sale_order = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id)])
        if sale_order:
            for sale in sale_order:
                if sale.invoice_ids:
                    if self.id in sale.invoice_ids.ids:
                        sale_id = sale.id
                        if sale_id:
                            for line in sale.payment_detail_ids:
                                if not line.payment_ids:
                                    pricelist_lines.append(line.payment_term_line_id.id)
                            if pricelist_lines:
                                milestone.append(pricelist_lines[0])
                                
        purchase_order = self.env['purchase.order'].search([('partner_id', '=', self.partner_id.id)])
        if purchase_order:
            for purchase in purchase_order:
                if purchase.invoice_ids:
                    if self.id in purchase.invoice_ids.ids:
                        purchase_id = purchase.id
                        if purchase_id:
                            for line in purchase.payment_detail_ids:
                                if not line.payment_ids:
                                    pricelist_lines.append(line.payment_term_line_id.id)
                            if pricelist_lines:
                                milestone.append(pricelist_lines[0])
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
                'default_sale_order_id': sale_id,
                'default_payment_term_line_ids': [(6, 0, milestone)],
                'default_purchase_order_id': purchase_id,
                'default_po_payment_term_line_ids': [(6, 0, milestone)]
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
        
    delivery_challan_no = fields.Char("Delivery Challan No")
    delivery_challan_date = fields.Date("Delivery Challan Date")
    courier = fields.Char("Dispatch through Carrier")
    awb = fields.Char("LR / GR / Docket ? AWB No")
    friegt = fields.Char("Freight Term")
    insurance = fields.Char("Insurance")
    rep_code = fields.Char("Report Code")
    po_ref = fields.Char("PO Ref")
    project_id = fields.Char("Project")

class Incoterm(models.Model):
    _inherit = "account.incoterms"
    
    amount = fields.Float("Amount")
    
    