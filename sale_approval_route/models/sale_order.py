# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_team_id = fields.Many2one(
        comodel_name="sale.team", string="Sale Order Type", domain="[('company_id', '=', company_id)]",
        readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},)

    approver_ids = fields.One2many(
        comodel_name="sale.order.approver", inverse_name="order_id", string="Approvers", readonly=True)

    current_approver = fields.Many2one(
        comodel_name="sale.order.approver", string="Approver",
        compute="_compute_approver", store=True, compute_sudo=True)

    next_approver = fields.Many2one(
        comodel_name="sale.order.approver", string="Next Approver",
        compute="_compute_approver", store=True, compute_sudo=True)

    is_current_approver = fields.Boolean(
        string="Is Current Approver", compute="_compute_is_current_approver"
    )

    lock_amount_total = fields.Boolean(
        string="Lock Amount Total", compute="_compute_lock_amount_total"
    )
    approval_required = fields.Boolean(related='so_team_id.approval_required', store=True)
    amount_total = fields.Monetary(tracking=True)
    state = fields.Selection(selection_add=[('to approve', 'To Approve')])
    kw = fields.Float("KWP", default=1.0, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},)
    order_type_id = fields.Many2one('sale.order.type', "Order Type")
    
    # @api.onchange('kw')
    # def onchange_kw(self):
    #     if self.kw:   
    #         if self.sale_order_template_id:
    #             self.onchange_sale_order_template_id()         
            # if self.order_line:
            #     for l in self.order_line:
            #         l.price_unit = l.per_kw * l.price_unit

    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #     if 'amount_total' in init_values and self.amount_total != init_values.get('amount_total'):
    #         self._check_lock_amount_total()
    #     return super(SaleOrder, self)._track_subtype(init_values)

    def button_approve(self, force=False):
        for order in self: 
            price = [] 
            for line in order.order_line:   
                price.append(line.product_id.lst_price)
                if order.pricelist_id:
                    plines = order.pricelist_id.item_ids.filtered(lambda l: l.product_tmpl_id.id == line.product_id.product_tmpl_id.id)
                    if plines:
                        for linea in plines:
                            price.append(linea.fixed_price)
                if price:
                    if line.price_unit not in price:    
                        if order.current_approver:
                            if order.current_approver.user_id == self.env.user or self.env.is_superuser():
                                # If current user is current approver (or superuser) update state as "approved"
                                order.current_approver.state = 'approved'
                                order.message_post(body=_('Sale approved by %s') % self.env.user.name)
                                # Check is there is another approver
                                if order.next_approver:
                                    # Send request to approve is there is next approver
                                    order.send_to_approve()
                                else:
                                    # If there is not next approval, than assume that approval is finished and send notification
                                    partner = order.user_id.partner_id if order.user_id else order.create_uid.partner_id
                                    order.message_post_with_view(
                                        'sale_approval_route.order_approval',
                                        subject=_('Sale Approved: %s') % (order.name,),
                                        composition_mode='mass_mail',
                                        partner_ids=[(4, partner.id)],
                                        auto_delete=True,
                                        auto_delete_message=True,
                                        parent_id=False,
                                        subtype_id=self.env.ref('mail.mt_note').id)
                                    # if self._get_forbidden_state_confirm() & set(self.mapped('state')):
                                    #     raise UserError(_(
                                    #         'It is not allowed to confirm an order in the following states: %s'
                                    #     ) % (', '.join(self._get_forbidden_state_confirm())))
                            
                                    for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
                                        order.message_subscribe([order.partner_id.id])
                                    self.write(self._prepare_confirmation_values())
                            
                                    # Context key 'default_name' is sometimes propagated up to here.
                                    # We don't need it and it creates issues in the creation of linked records.
                                    context = self._context.copy()
                                    context.pop('default_name', None)
                            
                                    self.with_context(context)._action_confirm()
                                    if self.env.user.has_group('sale.group_auto_done_setting'):
                                        self.action_done()
                                    # Do default behaviour to set state as "sale" and update date_approve
                            else:
                                # if self._get_forbidden_state_confirm() & set(self.mapped('state')):
                                #     raise UserError(_(
                                #         'It is not allowed to confirm an order in the following states: %s'
                                #     ) % (', '.join(self._get_forbidden_state_confirm())))
                        
                                for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
                                    order.message_subscribe([order.partner_id.id])
                                self.write(self._prepare_confirmation_values())
                        
                                # Context key 'default_name' is sometimes propagated up to here.
                                # We don't need it and it creates issues in the creation of linked records.
                                context = self._context.copy()
                                context.pop('default_name', None)
                        
                                self.with_context(context)._action_confirm()
                                if self.env.user.has_group('sale.group_auto_done_setting'):
                                    self.action_done()
                    else:
                        # if self._get_forbidden_state_confirm() & set(self.mapped('state')):
                        #     raise UserError(_(
                        #         'It is not allowed to confirm an order in the following states: %s'
                        #     ) % (', '.join(self._get_forbidden_state_confirm())))
                
                        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
                            order.message_subscribe([order.partner_id.id])
                        self.write(self._prepare_confirmation_values())
                
                        # Context key 'default_name' is sometimes propagated up to here.
                        # We don't need it and it creates issues in the creation of linked records.
                        context = self._context.copy()
                        context.pop('default_name', None)
                
                        self.with_context(context)._action_confirm()
                        if self.env.user.has_group('sale.group_auto_done_setting'):
                            self.action_done()
                            
                                                # self.action_done()
                else:
                    # if self._get_forbidden_state_confirm() & set(self.mapped('state')):
                    #     raise UserError(_(
                    #         'It is not allowed to confirm an order in the following states: %s'
                    #     ) % (', '.join(self._get_forbidden_state_confirm())))
            
                    for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
                        order.message_subscribe([order.partner_id.id])
                    self.write(self._prepare_confirmation_values())
            
                    # Context key 'default_name' is sometimes propagated up to here.
                    # We don't need it and it creates issues in the creation of linked records.
                    context = self._context.copy()
                    context.pop('default_name', None)
            
                    self.with_context(context)._action_confirm()
                    if self.env.user.has_group('sale.group_auto_done_setting'):
                        self.action_done()

    def action_confirm(self):
        for order in self:
            # if order.amount_total  > order.so_team_id.max_amount:
            #     raise UserError(_('Sale order Total exceeds maximum amount of Sale Type.'))
            # if order.incoterm and order.amount_total  > order.incoterm.amount:
            #     raise UserError(_('Sale order Total exceeds Incoterm amount.'))
            if order.state not in ['draft', 'sent']:
                continue
            if not order.so_team_id:
                # Do default behaviour if PO Team is not set
                super(SaleOrder, self).action_confirm()
            elif order.approval_required == False:
                super().action_confirm()
            else:
                # Generate approval route and send PO to approve
                order.generate_approval_route()
                if order.next_approver:
                    # If approval route is generated and there is next approver mark the order "to approve"
                    order.write({'state': 'to approve'})
                    # And send request to approve
                    order.send_to_approve()
                else:
                    # If there are not approvers, do default behaviour and move PO to the "Sale Order" state
                    order.button_approve()
            if order.incoterm and order.amount_total  > order.incoterm.amount:
                order.generate_approval_route()
                if order.next_approver:
                    # If approval route is generated and there is next approver mark the order "to approve"
                    order.write({'state': 'to approve'})
                    # And send request to approve
                    order.send_to_approve()
            # order._add_supplier_to_product()
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def generate_approval_route(self):
        """
        Generate approval route for order
        :return:
        """
        for order in self:
            if not order.so_team_id:
                continue
            if order.approver_ids:
                # reset approval route
                order.approver_ids.unlink()
            for team_approver in order.so_team_id.approver_ids:

                custom_condition = order.compute_custom_condition(team_approver)
                if not custom_condition:
                    # Skip approver, if custom condition for the approver is set and the condition result is not True
                    continue

                min_amount = team_approver.company_currency_id._convert(
                    team_approver.min_amount,
                    order.currency_id,
                    order.company_id,
                    order.date_order or fields.Date.today())
                if min_amount > order.amount_total:
                    # Skip approver if Minimum Amount is greater than Total Amount
                    continue
                max_amount = team_approver.company_currency_id._convert(
                    team_approver.max_amount,
                    order.currency_id,
                    order.company_id,
                    order.date_order or fields.Date.today())
                if max_amount and max_amount < order.amount_total:
                    # Skip approver if Maximum Amount is set and less than Total Amount
                    continue

                # Add approver to the PO
                self.env['sale.order.approver'].create({
                    'sequence': team_approver.sequence,
                    'team_id': team_approver.team_id.id,
                    'user_id': team_approver.user_id.id,
                    'role': team_approver.role,
                    'min_amount': team_approver.min_amount,
                    'max_amount': team_approver.max_amount,
                    'lock_amount_total': team_approver.lock_amount_total,
                    'order_id': order.id,
                    'team_approver_id': team_approver.id,
                })

    def compute_custom_condition(self, team_approver):
        self.ensure_one()
        localdict = {'PO': self, 'USER': self.env.user}
        if not team_approver.custom_condition_code:
            return True
        try:
            safe_eval(team_approver.custom_condition_code, localdict, mode='exec', nocopy=True)
            return bool(localdict['result'])
        except Exception as e:
            raise UserError(_('Wrong condition code defined for %s. Error: %s') % (team_approver.display_name, e))

    @api.depends('approver_ids.state')
    def _compute_approver(self):
        for order in self:
            next_approvers = order.approver_ids.filtered(lambda a: a.state == "to approve")
            order.next_approver = next_approvers[0] if next_approvers else False

            current_approvers = order.approver_ids.filtered(lambda a: a.state == "pending")
            order.current_approver = current_approvers[0] if current_approvers else False

    @api.depends('current_approver')
    def _compute_is_current_approver(self):
        for order in self:
            order.is_current_approver = ((order.current_approver and order.current_approver.user_id == self.env.user)
                                         or self.env.is_superuser())

    @api.depends('approver_ids.state', 'approver_ids.lock_amount_total')
    def _compute_lock_amount_total(self):
        for order in self:
            order.lock_amount_total = len(order.approver_ids.filtered(lambda a: a.state == "approved" and a.lock_amount_total)) > 0

    def send_to_approve(self):
        for order in self:
            if order.state != 'to approve' and not order.team_id:
                continue

            main_error_msg = _("Unable to send approval request to next approver.")
            if order.current_approver:
                reason_msg = _("The order must be approved by %s") % order.current_approver.user_id.name
                raise UserError("%s %s" % (main_error_msg, reason_msg))

            if not order.next_approver:
                reason_msg = _("There are no approvers in the selected PO team.")
                raise UserError("%s %s" % (main_error_msg, reason_msg))
            # use sudo as sale user cannot update sale.order.approver
            order.sudo().next_approver.state = 'pending'
            # Now next approver became as current
            current_approver_partner = order.current_approver.user_id.partner_id
            if current_approver_partner not in order.message_partner_ids:
                order.message_subscribe([current_approver_partner.id])
            order.with_user(order.user_id).message_post_with_view(
                'sale_approval_route.request_to_approve',
                subject=_('Sale Approval: %s') % (order.name,),
                composition_mode='mass_mail',
                partner_ids=[(4, current_approver_partner.id)],
                auto_delete=True,
                auto_delete_message=True,
                parent_id=False,
                subtype_id=self.env.ref('mail.mt_note').id)

class SaleOrder(models.Model):
    _inherit = "sale.order.line"    
    
    unit = fields.Float("Unit")
    per_kw = fields.Float("Per KW")
    kw = fields.Float(related='order_id.kw', store=True)
    partner_ids = fields.Many2many('res.partner', 'vendor_template_rel1e', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_rele', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    
    @api.onchange('product_id', 'kw', 'per_kw')
    def onchange_product(self):
        products = []
        if self.product_id:
            if self.product_id.seller_ids:
                for line in self.product_id.seller_ids:
                    products.append(line.name.id)
            self.partner_ids = [(6, 0, products)]
        if self.kw:
            self.price_unit = self.per_kw * self.kw
    
    @api.depends('kw', 'unit')
    def compute_per_kw(self):
        for rec in self:
            if rec.unit > 0.0:
                rec.per_kw = (rec.kw * 1000)/rec.unit
                
class SaleOrderOption(models.Model):
    _inherit = "sale.order.option"    
    
    partner_ids = fields.Many2many('res.partner', 'vendor_template_option_rel', 'vendor_id', 'template_id', "Make")
    vendor_ids = fields.Many2many('res.partner', 'vendor_template_option_rel', 'vendor_id', 'template_id', "Make")
    model = fields.Char("Model")
    
    @api.onchange('product_id')
    def onchange_product(self):
        products = []
        if self.product_id:
            if self.product_id.seller_ids:
                for line in self.product_id.seller_ids:
                    products.append(line.name.id)
            self.partner_ids = [(6, 0, products)]
