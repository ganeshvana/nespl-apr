# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = "hr.expense"
    
    eligible_amount = fields.Monetary(string='Eligible Amount', currency_field='currency_id',)
    approved_amount = fields.Monetary(string='Approved Amount', currency_field='currency_id',)
    employee_pin = fields.Char("Employee PIN", required=True)
    
    @api.onchange('approved_amount')
    def onchange_approved_amount(self):
        if self.approved_amount:
            self.total_amount = self.approved_amount
            
    @api.onchange('employee_pin', 'employee_id')
    def onchange_employee_pin(self):
        if self.employee_pin and not self.employee_id:
            raise ValidationError("Select Employee")
        # if self.employee_pin and self.employee_id:
        #     if self.employee_pin != self.employee_id.employee_pin:
        #         raise ValidationError("PIN is wrong!!!")
            
    def write(self, vals):
        res = super(HrExpense, self).write(vals)
        for rec in self:
            if rec.employee_id and not rec.employee_pin:
                raise ValidationError("Enter Employee PIN !!!")
            if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
                raise ValidationError("PIN is wrong!!!")
            if 'employee_pin' in vals:
                if rec.employee_id and rec.employee_pin != rec.employee_id.employee_pin:
                    raise ValidationError("PIN is wrong!!!")
        return res
           
    @api.model
    def _get_employee_id_domain(self):
        # res = [('id', '=', 0)] # Nothing accepted by domain, by default
        # if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups('account.group_account_user'):
        #     res = "['|', ('company_id', '=', False), ('company_id', '=', company_id)]"  # Then, domain accepts everything
        # elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and self.env.user.employee_ids:
        #     user = self.env.user
        #     employee = self.env.user.employee_id
        #     res = [
        #         '|', '|', '|',
        #         ('department_id.manager_id', '=', employee.id),
        #         ('parent_id', '=', employee.id),
        #         ('id', '=', employee.id),
        #         ('expense_manager_id', '=', user.id),
        #         '|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id),
        #     ]
        # elif self.env.user.employee_id:
        #     employee = self.env.user.employee_id
        #     res = [('id', '=', employee.id), '|', ('company_id', '=', False), ('company_id', '=', employee.company_id.id)]
        res = self.env['hr.employee'].search([])
        res = [('id', 'in', res.ids)]  
        return res
    
class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"
    
    
    @api.depends_context('uid')
    @api.depends('employee_id')
    def _compute_can_approve(self):
        is_approver = self.user_has_groups('hr_expense.group_hr_expense_team_approver, hr_expense.group_hr_expense_user')
        is_manager = self.user_has_groups('hr_expense.group_hr_expense_manager')
        for sheet in self:
            sheet.can_approve = is_manager 