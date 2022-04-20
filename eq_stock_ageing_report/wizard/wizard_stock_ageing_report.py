# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import xlsxwriter
import base64
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


class wizard_stock_ageing_report(models.TransientModel):
    _name = 'wizard.stock.ageing.report'
    _description = "Stock Ageing Report"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string='Location')
    start_date = fields.Date(string="Start Date")
    filter_by = fields.Selection([('product', 'Product'), ('category', 'Category')], string="Filter By")
    group_by_categ = fields.Boolean(string="Group By Category")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string='File', readonly=True)
    product_ids = fields.Many2many('product.product', string="Products")
    category_ids = fields.Many2many('product.category', string="Categories")
    period_length = fields.Integer(string="Period Length (Days)", default=30)

    @api.onchange('company_id')
    def onchange_company_id(self):
        domain = [('id', 'in', self.env.user.company_ids.ids)]
        if self.company_id:
            self.warehouse_ids = False
            self.location_ids = False
        return {'domain':{'company_id':domain}}

    @api.onchange('warehouse_ids')
    def onchange_warehouse_ids(self):
        stock_location_obj = self.env['stock.location']
        location_ids = stock_location_obj.search([('usage', '=', 'internal'), ('company_id', '=', self.company_id.id)])
        addtional_ids = []
        if self.warehouse_ids:
            for warehouse in self.warehouse_ids:
                addtional_ids.extend([y.id for y in stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')])])
            self.location_ids = False
        return {'domain':{'location_ids':[('id', 'in', addtional_ids)]}}

    @api.onchange('filter_by')
    def onchange_filter_by(self):
        self.product_ids = False
        self.category_ids = False

    def print_report(self):
        periods = self.get_periods()
        datas = {'form':
                    {
                        'company_id': self.company_id.id,
                        'warehouse_ids': [y.id for y in self.warehouse_ids],
                        'location_ids': self.location_ids.ids or False,
                        'start_date': self.start_date,
                        'id': self.id,
                        'product_ids': self.product_ids.ids,
                        'product_categ_ids': self.category_ids.ids,
                        'period':periods
                    },
                }
        return self.env.ref('eq_stock_ageing_report.action_stock_ageing_template').report_action(self, data=datas)

    def get_periods(self):
        periods = {}
        period_length = self.period_length
        if period_length<=0:
            raise UserError(_('You must set a period length greater than 0.'))
        start = fields.Date.from_string(self.start_date)
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        return periods

    def go_back(self):
        self.state = 'choose'
        return {
            'name': 'Stock Ageing Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    def print_xls_report(self):
        xls_filename = 'Stock Ageing Report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
        report_stock_inv_obj = self.env['report.eq_stock_ageing_report.stock_ageing_report']

        header_merge_format = workbook.add_format({'bold':True, 'align':'center', 'valign':'vcenter', \
                                            'font_size':10, 'bg_color':'#D3D3D3', 'border':1})

        header_data_format = workbook.add_format({'align':'center', 'valign':'vcenter', \
                                                   'font_size':10, 'border':1})

        product_header_format = workbook.add_format({'valign':'vcenter', 'font_size':10, 'border':1})

        periods = self.get_periods()
        for warehouse in self.warehouse_ids:
            worksheet = workbook.add_worksheet(warehouse.name)
            worksheet.merge_range(0, 0, 2, 8, "Stock Ageing Report", header_merge_format)

            worksheet.set_column('A:B', 18)
            worksheet.set_column('C:H', 12)
            worksheet.write(5, 0, 'Company', header_merge_format)
            worksheet.write(5, 1, 'Warehouse', header_merge_format)
            worksheet.write(5, 2, 'Start Date', header_merge_format)
            worksheet.write(5, 3, 'Period Length', header_merge_format)

            worksheet.write(6, 0, self.company_id.name, header_data_format)
            worksheet.write(6, 1, warehouse.name, header_data_format)
            worksheet.write(6, 2, self.start_date.strftime('%d-%m-%Y'), header_data_format)
            worksheet.write(6, 3, str(self.period_length) + ' Days', header_data_format)

            if not self.location_ids:
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, periods['4']['name'], header_merge_format)
                worksheet.write(9, 3, periods['3']['name'], header_merge_format)
                worksheet.write(9, 4, periods['2']['name'], header_merge_format)
                worksheet.write(9, 5, periods['1']['name'], header_merge_format)
                worksheet.write(9, 6, periods['0']['name'], header_merge_format)
                worksheet.write(9, 7, "Total", header_merge_format)

                rows = 10
                sum_column4 = sum_column3 = sum_column2 = sum_column1 = sum_column0 = sum_total_qty = 0.00
                if not self.group_by_categ:
                    for product in report_stock_inv_obj._get_products(self):
                        product_val = report_stock_inv_obj._get_ageing_inventory(self, product, warehouse,periods)
                        column4 = product_val.get(4)
                        column3 = product_val.get(3)
                        column2 = product_val.get(2)
                        column1 = product_val.get(1)
                        column0 = product_val.get(0)
                        total_qty = product_val.get('total_qty')

                        worksheet.merge_range(rows, 0, rows, 1, product.display_name, product_header_format)
                        worksheet.write(rows, 2, column4, header_data_format)
                        worksheet.write(rows, 3, column3, header_data_format)
                        worksheet.write(rows, 4, column2, header_data_format)
                        worksheet.write(rows, 5, column1, header_data_format)
                        worksheet.write(rows, 6, column0, header_data_format)
                        worksheet.write(rows, 7, total_qty, header_data_format)

                        sum_column4 += column4
                        sum_column3 += column3
                        sum_column2 += column2
                        sum_column1 += column1
                        sum_column0 += column0
                        sum_total_qty += total_qty
                        rows += 1

                    worksheet.merge_range(rows + 1, 0, rows + 1, 1, 'Total', header_merge_format)
                    worksheet.write(rows + 1, 2, sum_column4, header_merge_format)
                    worksheet.write(rows + 1, 3, sum_column3, header_merge_format)
                    worksheet.write(rows + 1, 4, sum_column2, header_merge_format)
                    worksheet.write(rows + 1, 5, sum_column1, header_merge_format)
                    worksheet.write(rows + 1, 6, sum_column0, header_merge_format)
                    worksheet.write(rows + 1, 7, sum_total_qty, header_merge_format)

                else:
                    rows += 1
                    for category in report_stock_inv_obj._get_product_category(self):
                        worksheet.merge_range(rows, 0, rows, 7, category.name, header_merge_format)
                        rows += 1
                        sum_categ_column4 = sum_categ_column3 = sum_categ_column2 = sum_categ_column1 = sum_categ_column0 = sum_categ_total_qty = 0.00
                        for product in report_stock_inv_obj._get_products(self,category):
                            product_val = report_stock_inv_obj._get_ageing_inventory(self, product, warehouse,periods)
                            column4 = product_val.get(4)
                            column3 = product_val.get(3)
                            column2 = product_val.get(2)
                            column1 = product_val.get(1)
                            column0 = product_val.get(0)
                            total_qty = product_val.get('total_qty')

                            worksheet.merge_range(rows, 0 , rows, 1, product.display_name, product_header_format)
                            worksheet.write(rows, 2, column4, header_data_format)
                            worksheet.write(rows, 3, column3, header_data_format)
                            worksheet.write(rows, 4, column2, header_data_format)
                            worksheet.write(rows, 5, column1, header_data_format)
                            worksheet.write(rows, 6, column0, header_data_format)
                            worksheet.write(rows, 7, total_qty, header_data_format)

                            sum_categ_column4 += column4
                            sum_categ_column3 += column3
                            sum_categ_column2 += column2
                            sum_categ_column1 += column1
                            sum_categ_column0 += column0
                            sum_categ_total_qty += total_qty
                            rows += 1

                        worksheet.merge_range(rows, 0 , rows, 1, 'Total', header_merge_format)
                        worksheet.write(rows, 2, sum_categ_column4, header_merge_format)
                        worksheet.write(rows, 3, sum_categ_column3, header_merge_format)
                        worksheet.write(rows, 4, sum_categ_column2, header_merge_format)
                        worksheet.write(rows, 5, sum_categ_column1, header_merge_format)
                        worksheet.write(rows, 6, sum_categ_column0, header_merge_format)
                        worksheet.write(rows, 7, sum_categ_total_qty, header_merge_format)
                        rows += 2
            else:
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, "Location", header_merge_format)
                worksheet.write(9, 3, periods['4']['name'], header_merge_format)
                worksheet.write(9, 4, periods['3']['name'], header_merge_format)
                worksheet.write(9, 5, periods['2']['name'], header_merge_format)
                worksheet.write(9, 6, periods['1']['name'], header_merge_format)
                worksheet.write(9, 7, periods['0']['name'], header_merge_format)
                worksheet.write(9, 8, "Total", header_merge_format)

                rows = 10
                sum_column4 = sum_column3 = sum_column2 = sum_column1 = sum_column0 = sum_total_qty = 0.00
                location_ids = report_stock_inv_obj.get_warehouse_wise_location(self, warehouse)
                if not self.group_by_categ:
                    for product in report_stock_inv_obj._get_products(self):
                        location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product, location_ids,periods)

                        column4 = location_wise_data[1][4]
                        column3 = location_wise_data[1][3]
                        column2 = location_wise_data[1][2]
                        column1 = location_wise_data[1][1]
                        column0 = location_wise_data[1][0]
                        total_qty = location_wise_data[1][5]

                        worksheet.merge_range(rows, 0, rows, 1, product.display_name, product_header_format)
                        worksheet.write(rows, 2, '', header_data_format)
                        worksheet.write(rows, 3, column4, header_merge_format)
                        worksheet.write(rows, 4, column3, header_merge_format)
                        worksheet.write(rows, 5, column2, header_merge_format)
                        worksheet.write(rows, 6, column1, header_merge_format)
                        worksheet.write(rows, 7, column0, header_merge_format)
                        worksheet.write(rows, 8, total_qty, header_merge_format)
                        rows += 1

                        for location, value in location_wise_data[0].items():
                            worksheet.merge_range(rows, 0, rows, 1, '', header_data_format)
                            worksheet.write(rows, 2, location.display_name, header_data_format)
                            worksheet.write(rows, 3, value[4], header_data_format)
                            worksheet.write(rows, 4, value[3], header_data_format)
                            worksheet.write(rows, 5, value[2], header_data_format)
                            worksheet.write(rows, 6, value[1], header_data_format)
                            worksheet.write(rows, 7, value[0], header_data_format)
                            worksheet.write(rows, 8, value['total_qty'], header_data_format)
                            rows += 1

                        sum_column4 += column4
                        sum_column3 += column3
                        sum_column2 += column2
                        sum_column1 += column1
                        sum_column0 += column0
                        sum_total_qty += total_qty

                    rows += 1
                    worksheet.merge_range(rows, 0, rows, 1, 'Total', header_merge_format)
                    worksheet.write(rows, 2, '', header_merge_format)
                    worksheet.write(rows, 3, sum_column4, header_merge_format)
                    worksheet.write(rows, 4, sum_column3, header_merge_format)
                    worksheet.write(rows, 5, sum_column2, header_merge_format)
                    worksheet.write(rows, 6, sum_column1, header_merge_format)
                    worksheet.write(rows, 7, sum_column0, header_merge_format)
                    worksheet.write(rows, 8, sum_total_qty, header_merge_format)

                else:
                    for category in report_stock_inv_obj._get_product_category(self):
                        worksheet.merge_range(rows, 0, rows, 8, category.name, header_merge_format)
                        rows += 1
                        sum_categ_column4 = sum_categ_column3 = sum_categ_column2 = sum_categ_column1 = sum_categ_column0 = sum_categ_total_qty = 0.00
                        for product in report_stock_inv_obj._get_products(self,category):
                            location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product, location_ids,periods)

                            column4 = location_wise_data[1][4]
                            column3 = location_wise_data[1][3]
                            column2 = location_wise_data[1][2]
                            column1 = location_wise_data[1][1]
                            column0 = location_wise_data[1][0]
                            total_qty = location_wise_data[1][5]

                            worksheet.merge_range(rows, 0, rows, 1, product.display_name, product_header_format)
                            worksheet.write(rows, 2, '', header_data_format)
                            worksheet.write(rows, 3, column4, header_merge_format)
                            worksheet.write(rows, 4, column3, header_merge_format)
                            worksheet.write(rows, 5, column2, header_merge_format)
                            worksheet.write(rows, 6, column1, header_merge_format)
                            worksheet.write(rows, 7, column0, header_merge_format)
                            worksheet.write(rows, 8, total_qty, header_merge_format)
                            rows += 1

                            for location, value in location_wise_data[0].items():
                                worksheet.merge_range(rows, 0, rows, 1, '', header_data_format)
                                worksheet.write(rows, 2, location.display_name, header_data_format)
                                worksheet.write(rows, 3, value[4], header_data_format)
                                worksheet.write(rows, 4, value[3], header_data_format)
                                worksheet.write(rows, 5, value[2], header_data_format)
                                worksheet.write(rows, 6, value[1], header_data_format)
                                worksheet.write(rows, 7, value[0], header_data_format)
                                worksheet.write(rows, 8, value['total_qty'], header_data_format)
                                rows += 1

                            sum_categ_column4 += column4
                            sum_categ_column3 += column3
                            sum_categ_column2 += column2
                            sum_categ_column1 += column1
                            sum_categ_column0 += column0
                            sum_categ_total_qty += total_qty
                            rows += 1

                        worksheet.merge_range(rows, 0, rows , 1, "Total", header_merge_format)
                        worksheet.write(rows, 2, '', header_merge_format)
                        worksheet.write(rows, 3, sum_categ_column4, header_merge_format)
                        worksheet.write(rows, 4, sum_categ_column3, header_merge_format)
                        worksheet.write(rows, 5, sum_categ_column2, header_merge_format)
                        worksheet.write(rows, 6, sum_categ_column1, header_merge_format)
                        worksheet.write(rows, 7, sum_categ_column0, header_merge_format)
                        worksheet.write(rows, 8, sum_categ_total_qty, header_merge_format)
                        rows += 2

        workbook.close()
        self.write({
            'state': 'get',
            'data': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read()),
            'name': xls_filename
        })
        return {
            'name': 'Stock Ageing Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: