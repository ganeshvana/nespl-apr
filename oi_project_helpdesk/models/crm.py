from odoo import models, fields, api, _

class Survey(models.Model):
    _inherit = 'survey.survey'
    
    crm_id = fields.Many2one('crm.lead', "Lead")
    
class SurveyAns(models.Model):
    _inherit = 'survey.user_input'
    
    crm_id = fields.Many2one(related='survey_id.crm_id', store=True)
    

class Lead(models.Model):
    _inherit = 'crm.lead'
    
    survey_id = fields.Many2one('survey.survey', "Questionnaire")
    employee_id = fields.Many2one('hr.employee', "Assigned To", tracking=True, track_visiblity = 'onchange')
    employee_pin = fields.Char("Employee PIN")
    roof_type = fields.Many2one('roof.type', "Roof Type")
    
    @api.onchange('employee_pin', 'employee_id')
    def onchange_employee_pin(self):
        if self.employee_pin and not self.employee_id:
            raise ValidationError("Select Employee")
        # if self.employee_pin and self.employee_id:
        #     if self.employee_pin != self.employee_id.employee_pin:
        #         raise ValidationError("PIN is wrong!!!")
        
    # def write(self, vals):
    #     res = super(Lead, self).write(vals)
    #     for rec in self:
    #         if rec.employee_id and not rec.employee_pin:
    #             raise ValidationError("Enter Employee PIN !!!")
    #         if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
    #             raise ValidationError("PIN is wrong!!!")
    #         if 'employee_pin' in vals:
    #             if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
    #                 raise ValidationError("PIN is wrong!!!")
    #     return res
    
    def need_analysis_form(self):
        survey = self.survey_id
        if survey:
            self.survey_id = survey.id
            survey.crm_id = self.id
            survey.action_test_survey()
            return {
                'type': 'ir.actions.act_url',
                'name': "Need Analysis",
                'target': '_blank',
                'url': '/survey/test/%s' % survey.access_token,
            }
    
    def action_view_project_ids(self):
        self.ensure_one()
        view_form_id = self.env.ref('project.edit_project').id
        view_kanban_id = self.env.ref('project.view_project_kanban').id
        projects = []
        for quotation in self.order_ids:
            if quotation.project_ids:
                for project in quotation.project_ids:
                    projects.append(project.id)
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', projects)],
            'view_mode': 'kanban,form',
            'name': _('Projects'),
            'res_model': 'project.project',
        }
        if len(projects) == 1:
            action.update({'views': [(view_form_id, 'form')], 'res_id': projects[0]})
        else:
            action['views'] = [(view_kanban_id, 'kanban'), (view_form_id, 'form')]
        return action
    
    def action_view_survey_answer(self):
        self.ensure_one()
        view_form_id = self.env.ref('survey.survey_user_input_view_form').id
        tree_form_id = self.env.ref('survey.survey_user_input_view_tree').id
        answer = []
        answer = self.env['survey.user_input'].search([('crm_id', '=', self.id)])
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', answer.ids)],
            'view_mode': 'form',
            'name': _('Answer'),
            'res_model': 'survey.user_input',
        }
        if len(answer) == 1:
            action.update({'views': [(view_form_id, 'form')], 'res_id': answer[0]})
        else:
            action['views'] = [(tree_form_id, 'tree'), (view_form_id, 'form')]
        return action
    
class Partner(models.Model):
    _inherit = 'res.partner'

    pan = fields.Char("PAN")
    
    @api.model_create_multi
    def create(self, vals_list):
        result = super(Partner, self).create(vals_list)
        for res in result:
            if res.customer_rank > 0:
                seq = self.env['ir.sequence'].next_by_code('customer.code.seq') or '/'
                res.ref = seq   
            if res.supplier_rank > 0:
                seq = self.env['ir.sequence'].next_by_code('vendor.code.seq') or '/'
                res.ref = seq        
        return result
    
    @api.onchange('state_id')
    def onchange_state_id(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id
    
    

class RoofType(models.Model):
    _name = 'roof.type'   
    
    name = fields.Char("Roof Type")
    
    
    
    