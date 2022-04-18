# -*- coding: utf-8 -*-
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

states = [('draft', 'Draft'), ('approved', 'Approved')]

class HrEmployee(models.Model):
    _inherit = "hr.employee"
    
    aadhaar = fields.Char("Aadhaar Number")
    blood_group = fields.Selection([('a+', 'A+'), ('b+', 'B+'),('o+', 'O+'),('ab+', 'AB+'), 
                                    ('a-', 'A-'), ('b-', 'B-'),('o-', 'O-'),('ab-', 'AB-'), 
                                    ],"Blood Group")
    vaccinedate1 = fields.Date("Vaccine 1 Date ")
    vaccinedate2 = fields.Date("Vaccine 2 Date ")
    boosterdate = fields.Date("Booster Date ")
    allergic = fields.Char("Allergic to any")
    employee_pin = fields.Char("PIN")
    user_id = fields.Many2one('res.users', 'User', store=True, readonly=False)
    
class HrEmployeeP(models.Model):
    _inherit = "hr.employee.public"
    
    aadhaar = fields.Char("Aadhaar Number")
    blood_group = fields.Selection([('a+', 'A+'), ('b+', 'B+'),('o+', 'O+'),('ab+', 'AB+'), 
                                    ('a-', 'A-'), ('b-', 'B-'),('o-', 'O-'),('ab-', 'AB-'), 
                                    ],"Blood Group")
    vaccinedate1 = fields.Date("Vaccine 1 Date ")
    vaccinedate2 = fields.Date("Vaccine 2 Date ")
    boosterdate = fields.Date("Booster Date ")
    allergic = fields.Char("Allergic to any")
    employee_pin = fields.Char("PIN")
    user_id = fields.Many2one('res.users', 'User', store=True, readonly=False)