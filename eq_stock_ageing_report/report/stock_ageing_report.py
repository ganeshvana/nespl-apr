# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

import pytz
import time
from operator import itemgetter
from itertools import groupby
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, date
from odoo.exceptions import Warning


class eq_stock_ageing_report_stock_ageing_report(models.AbstractModel):
    _name = 'report.eq_stock_ageing_report.stock_ageing_report'
    _description = "Stock Ageing Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('eq_stock_ageing_report.action_stock_ageing_template')
        record_id = data['form']['id'] if data and data['form'] and data['form']['id'] else docids[0]
        records = self.env['wizard.stock.ageing.report'].browse(record_id)
        return {
           'doc_model': report.model,
           'docs': records,
           'data': data,
           'get_ageing_inventory': self._get_ageing_inventory,
           'get_products':self._get_products,
           'get_location_wise_product':self.get_location_wise_product,
           'get_warehouse_wise_location':self.get_warehouse_wise_location,
           'get_product_category':self._get_product_category
        }

    def get_warehouse_wise_location(self, record, warehouse):
        stock_location_obj = self.env['stock.location']
        location_ids = stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id)])
        final_location_ids = record.location_ids & location_ids
        return final_location_ids or location_ids

    def get_location_wise_product(self, record, warehouse, product, location_ids, periods,product_categ_id=None):
        group_by_location = {}
        column_0 = column_1 = column_2 = column_3 = column_4 = column_5 = total = 0.00
        for location in location_ids:
            group_by_location.setdefault(location, False)
            res = (self._get_ageing_inventory(record, product, warehouse, periods, [location.id]))
            group_by_location[location] = res
            column_0 += res.get(0)
            column_1 += res.get(1)
            column_2 += res.get(2)
            column_3 += res.get(3)
            column_4 += res.get(4)
            total += res.get('total_qty')
        return group_by_location,[column_0,column_1,column_2,column_3,column_4,total]

    def get_location(self, records, warehouse):
        stock_location_obj = self.env['stock.location'].sudo()
        location_ids = []
        location_ids.append(warehouse.view_location_id.id)
        domain = [('company_id', '=', records.company_id.id), ('usage', '=', 'internal'), ('location_id', 'child_of', location_ids)]
        final_location_ids = stock_location_obj.search(domain).ids
        return final_location_ids

    def _get_products(self, record,category=None):
        product_product_obj = self.env['product.product']
        domain = [('type', '=', 'product')]
        if category:
            domain += [('categ_id','=',category.id)]
        product_ids = False
        if record.category_ids and not category:
            domain.append(('categ_id', 'in', record.category_ids.ids))
            product_ids = product_product_obj.search(domain)
        if record.product_ids:
            product_ids = record.product_ids
        if not product_ids:
             product_ids = product_product_obj.search(domain)
        if category:
            product_ids = product_ids.filtered(lambda l:l.categ_id.id == category.id)
        return product_ids

    def _get_product_category(self,record):
        category_ids = False
        if record.category_ids:
            category_ids = record.category_ids
        else:
            category_ids = self.env['product.category'].search([])
        if record.product_ids:
            category_ids = category_ids.filtered(lambda l:l.id in record.product_ids.mapped('categ_id').ids)
        return category_ids

    def _get_ageing_inventory(self, record, product, warehouse, periods,location=None):
        final_dict = {0:0,1:0,2:0,3:0,4:0,'total_qty':0}
        total_qty = 0.00
        locations = location if location else self.get_location(record, warehouse)
        if not product:
            return final_dict

        product_id = product.id

        for i in range(5):
            args_list = (tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), tuple(locations), product_id,record.company_id.id)
            dates_query = '(COALESCE(smline.date)::date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s'
                args_list += (periods[str(i)]['stop'],)

            query_res = []
            query = """
                SELECT pp.id AS product_id,pt.categ_id,

                    sum((
                    CASE WHEN spt.code in ('outgoing') AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory'
                    THEN -(smline.qty_done * pu.factor / pu2.factor)
                    ELSE 0.0 
                    END
                    )) AS product_qty_out,

                    sum((
                    CASE WHEN spt.code in ('incoming') AND smline.location_dest_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                    THEN (smline.qty_done * pu.factor / pu2.factor) 
                    ELSE 0.0 
                    END
                    )) AS product_qty_in,

                    sum((
                    CASE WHEN (spt.code ='internal') AND smline.location_dest_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                    THEN (smline.qty_done * pu.factor / pu2.factor)  
                    WHEN (spt.code ='internal' OR spt.code is null) AND smline.location_id in %s AND sourcel.usage !='inventory' AND destl.usage !='inventory' 
                    THEN -(smline.qty_done * pu.factor / pu2.factor) 
                    ELSE 0.0 
                    END
                    )) AS product_qty_internal,

                    sum((
                    CASE WHEN sourcel.usage = 'inventory' AND smline.location_dest_id in %s  
                    THEN  (smline.qty_done * pu.factor / pu2.factor)
                    WHEN destl.usage ='inventory' AND smline.location_id in %s 
                    THEN -(smline.qty_done * pu.factor / pu2.factor)
                    ELSE 0.0 
                    END
                    )) AS product_qty_adjustment

                FROM product_product pp
                LEFT JOIN stock_move sm ON (sm.product_id = pp.id and sm.state = 'done')
                LEFT JOIN stock_move_line smline ON (smline.product_id = pp.id and smline.state = 'done' and smline.location_id != smline.location_dest_id and smline.move_id = sm.id)
                LEFT JOIN stock_picking sp ON (sm.picking_id=sp.id)
                LEFT JOIN stock_picking_type spt ON (spt.id=sp.picking_type_id)
                LEFT JOIN stock_location sourcel ON (smline.location_id=sourcel.id)
                LEFT JOIN stock_location destl ON (smline.location_dest_id=destl.id)
                LEFT JOIN uom_uom pu ON (sm.product_uom=pu.id)
                LEFT JOIN uom_uom pu2 ON (sm.product_uom=pu2.id)
                LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
                WHERE pp.id = %s and sm.company_id = %s
                AND """ + dates_query + """
                GROUP BY pt.categ_id, pp.id order by pt.categ_id
            """

            self._cr.execute(query, args_list)
            query_res = self._cr.dictfetchone()
            if query_res:
                final_qty = query_res['product_qty_in'] + query_res['product_qty_out'] + \
                    query_res['product_qty_internal'] + query_res['product_qty_adjustment']
                total_qty += final_qty
                final_dict[i] = final_qty

        final_dict['total_qty'] = total_qty
        return final_dict

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
