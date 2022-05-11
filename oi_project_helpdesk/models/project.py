# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging
import base64
_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    # def create(self, vals):
    #     record = super(Attachment, self).create(vals)   
    #     decoded_file_size = tot_decoded_file_size = 0
    #     if record.datas:
    #         decoded = base64.b64decode(record.datas)
    #         decoded_file_size = decoded_file_size + len(decoded)
    #
    #         tot_decoded_file_size = (decoded_file_size/1024/1024)
    #         if tot_decoded_file_size > 5: 
    #             user_ref_rec = self.env.user
    #             notify_msg = 'The Attachment size exceeds. the max size is 5MB'
    #             notify_title = "Data - Warning"
    #             user_ref_rec.notify_info(notify_msg,notify_title,False)
    #
    #     return record
    
    # def _post_add_create(self):
    #     """ Overrides behaviour when the attachment is created through the controller
    #     """
    #     super(Attachment, self)._post_add_create()
    #     for record in self:
    #         record.register_as_main_attachment(force=False)
    #         decoded_file_size = tot_decoded_file_size = 0
    #         print(record.datas, "==============res.datas")
    #         if record.datas:
    #             decoded = base64.b64decode(record.datas)
    #             decoded_file_size = decoded_file_size + len(decoded)
    #
    #             tot_decoded_file_size = (decoded_file_size/1024/1024)
    #             print(tot_decoded_file_size, "===========rf")
    #             if tot_decoded_file_size > 5:
    #                 # raise ValidationError("The Attachment size exceeds. the max size is 5MB")
    #                 return {
    #                 'type': 'ir.actions.client',
    #                 'tag': 'display_notification',
    #                 'params': {
    #                     'title': _('The Attachment size exceeds. the max size is 5MB'),
    #                     'message': 'The Attachment size exceeds. the max size is 5MB',
    #
    #                     'sticky': False,
    #                 }
    #             }
    
class Project(models.Model):
    _inherit = 'project.project'
    
    project_lifelines = fields.Integer("Lifelines")
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    project_number = fields.Char("Project Number")
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    country_code = fields.Char(related='country_id.code', string="Country Code")
    partner_latitude = fields.Float(string='Geo Latitude', digits=(10, 7))
    partner_longitude = fields.Float(string='Geo Longitude', digits=(10, 7))
    
    # def create(self, vals):
    #     res = super(Project, self).create(vals)
    #     seq = self.env['ir.sequence'].next_by_code('project.code.seq') or ''
    #     res.project_number = seq
    #     res.name = seq
    #     return res
    
    def name_get(self):
        result = []
        string = ''
        for line in self:
            if line.project_number:
                name = line.project_number
            else:
                name =  line.name
            result.append((line.id, name))
        return result
    
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    project_lifelines = fields.Integer(string="Total Lifelines")
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    
    