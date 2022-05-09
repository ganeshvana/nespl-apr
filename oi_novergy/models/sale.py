from odoo import api, fields, models, tools, _

class salevendors(models.Model):
    _name = "sale.vendors"
    _description = "Sale vendors"

    name = fields.Many2one('res.partner', string="CLIENT NAME", copy=False)
    


class salevendors(models.Model):
    _inherit = "sale.vendors"


    # client_name = fields.Many2one('res.partner',string="CLIENT NAME", copy=False)
    site_location = fields.Char(string="SITE/LOCATION", copy=False)
    project_no = fields.Many2one('res.partner',string="Novergy Project No", copy=False)
    project_capacity = fields.Float(string="PROJECT Capacity", copy=False)
    Type_of_reading = fields.Selection([('monthly', 'Monthly'), ('year', 'Yearly'), ('quarterly', 'Quarterly')], string="Type of Reading", copy=False)
    energy_for_month = fields.Date(string="ENERGY FOR THE MONTH & YEAR", copy=False)
    date_of_reading = fields.Datetime(string="Date of Reading", copy=False)
    solar_energy_meter = fields.Many2one('res.partner', string="SOLAR ENERGY METER MAKE", copy=False)
    solar_energy_meter_model = fields.Char(string="SOLAR ENERGY METER MAKE MODEL", copy=False)
    solar_energy_meter_sr = fields.Char(string="SOLAR ENERGY METER SR.NO", copy=False)
    ct_ratio = fields.Float(string="CT RATIO", copy=False)
    multiplication_factor = fields.Float(string="MULTIPLICATION FACTOR", copy=False)
    meter_voltage = fields.Char(string="METER VOLTAGE LEVEL", copy=False)
    bill_reading1 = fields.Float(string="01 BILL reading(KWH)", copy=False)
    bill_reading2 = fields.Float(string="02 BILL reading(KWH)", copy=False)
    differece = fields.Float(string="DIFFERENCE (KWH)", copy=False)
    multiplication_factor_energy = fields.Float(string="Energy with Multiplication factor (KWH)", copy=False)
    total_solar_energy = fields.Float(string="TOTAL SOLAR ENERGY FOR MONTH (in Figures)", copy=False)
    total_solar_energy_month  = fields.Integer(string="TOTAL SOLAR ENERGY FOR MONTH (in WORDS)", copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

