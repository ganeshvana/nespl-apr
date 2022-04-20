from odoo import api,fields,models,_
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, AccessError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class sale_order(models.Model):
    _inherit = 'sale.order'
    
    state = fields.Selection([
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),           
            ('sale', 'Sales Order'),
            ('proforma_invoice','Proforma Invoice Sent'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled'),
            ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    def action_view_lines(self):
        line_ids = []
        action = self.env.ref('oodu_abc_sale_extended.action_order_lines').read()[0]
        line_search = self.env['sale.order.line'].search([('order_id', '=', self.id)])
        for data in line_search:
            line_ids.append(data.id)
 
        action['domain'] = [('id', 'in', line_ids)]
        return action


    def action_send_proforma(self):
        self.write({'state':'proforma_invoice'})


    
    # @api.depends('state', 'order_line.invoice_status')
    # def _get_invoiced(self):
            
    #     for order in self:
    #         invoice_ids = order.order_line.mapped('invoice_lines').mapped('move_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
    #         refunds = invoice_ids.search([('invoice_origin', 'like', order.name), ('company_id', '=', order.company_id.id)]).filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
    #         invoice_ids |= refunds.filtered(lambda r: order.name in [invoice_origin.strip() for invoice_origin in r.invoice_origin.split(',')])
    #         refund_ids = self.env['account.move'].browse()
    #         if invoice_ids:
    #             for inv in invoice_ids:
    #                 refund_ids += refund_ids.search([('type', '=', 'out_refund'), ('invoice_origin', '=', inv.number), ('invoice_origin', '!=', False), ('journal_id', '=', inv.journal_id.id)])
    #         deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
    #         line_invoice_status = [line.invoice_status for line in order.order_line if line.product_id != deposit_product_id]

    #         if order.state not in ('sale', 'done', 'proforma_invoice'):
    #             invoice_status = 'no'
    #         elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
    #             invoice_status = 'to invoice'
    #         elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
    #             invoice_status = 'invoiced'
    #         elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
    #             invoice_status = 'upselling'
    #         else:
    #             invoice_status = 'no'


    #         order.update({
    #             'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
    #             'invoice_ids': invoice_ids.ids + refund_ids.ids,
    #             'invoice_status': invoice_status
    #         })

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices
            order.invoice_count = len(invoices)

class sale_order_line(models.Model):
    _inherit = "sale.order.line"
    partner_id = fields.Many2one('res.partner', string="Customer")
    proforma_invoice = fields.Boolean('PI')
    proforma_invoiced = fields.Boolean('Proforma Invoiced')
   
    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done', 'proforma_invoice'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            elif line.state == 'proforma_invoice' and line.qty_invoiced > 0:
                line.invoice_status = 'invoiced'
            elif line.state == 'proforma_invoice' and line.qty_invoiced == 0:
                line.invoice_status = 'to invoice'
            else:
                line.invoice_status = 'no'

 
    def action_pi(self):
        for record in self:
            if record.proforma_invoiced==True:
                raise UserError(_('The line is already proforma invoiced'))
            if record.proforma_invoice==True:
                record.write({'proforma_invoiced':True})
            if not record.proforma_invoiced and not record.proforma_invoice:
                raise UserError(_('Cannot consider as proforma invoiced without enabling PI'))


    
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):

        for line in self:
            if line.order_id.state in ['sale', 'done', 'proforma_invoice']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
