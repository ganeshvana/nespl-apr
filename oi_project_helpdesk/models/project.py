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

    def create(self, vals):
        record = super(Attachment, self).create(vals)   
        decoded_file_size = tot_decoded_file_size = 0
        print(record.datas, "==============res.datas")
        if record.datas:
            decoded = base64.b64decode(record.datas)
            decoded_file_size = decoded_file_size + len(decoded)

            tot_decoded_file_size = (decoded_file_size/1024/1024)
            print(tot_decoded_file_size, "===========rf")
            if tot_decoded_file_size > 5: 
                user_ref_rec = self.env.user
                print(user_ref_rec, "user_ref_rec-----------")
                notify_msg = 'The Attachment size exceeds. the max size is 5MB'
                notify_title = "Data - Warning"
                user_ref_rec.notify_info(notify_msg,notify_title,False)
    
        return record
    
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
    
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    project_lifelines = fields.Integer(related='project_id.project_lifelines',string="Total Lifelines", store=True)
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    
    