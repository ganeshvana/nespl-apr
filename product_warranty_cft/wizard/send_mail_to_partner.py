from odoo import api,fields, models

class SendMailPartner(models.TransientModel):
    _name = "send.mail.partner"
    _description = 'Send Mail Partner'


    def active_model_template(self):
        models = self.env['ir.model'].search([('model','=',self.env.context.get('active_model'))])

        return [('model_id','in',models.ids)]

    mail_template_id = fields.Many2one('mail.template',string='Mail Template',domain=active_model_template)

    
    def send_mail(self):

        if self.env.context.get('active_model')=='claim.warranty':
            claim = self.env['claim.warranty'].search([('id','=',self.env.context.get('active_id'))])
            self.mail_template_id.send_mail(claim.id)
        if self.env.context.get('active_model')=='warranty.card':
            warranty_card = self.env['warranty.card'].search([('id','=',self.env.context.get('active_id'))])
            self.mail_template_id.send_mail(warranty_card.id)
        return True

