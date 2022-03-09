# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('quotation_submit', 'Quotation Submit'),
        ('quotation_approved', 'Quotation Approved'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('agreement_submit', 'Agreement Submitted'),
        ('submit_client_operation', 'Submit Client To operation'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')

    qshield_crm_state = fields.Selection(related="state")
    approver_setting_id = fields.Many2one("sale.order.approver.settings", compute="compute_approver_settings_id")
    approver_ids = fields.One2many('sale.order.approver', 'sale_order_id', string="Approvers")
    account_manager = fields.Many2one('hr.employee', string="Account Manager")
    due_date = fields.Date(string="Due Date")
    user_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel')], compute="_compute_user_status")
    is_approver_user = fields.Boolean(compute="compute_is_approver_user")
    refuse_quotation_reason = fields.Text(string="Refuse Quotation Reason")
    refuse_agreement_reason = fields.Text(string="Refuse Agreement Reason")
    is_valid_for_agreement = fields.Boolean(compute='compute_is_valid_for_agreement')
    invoice_term_ids = fields.One2many('invoice.term.line', 'sale_id', 'Invoicing Terms')
    is_agreement = fields.Selection([('is_retainer', 'Is Retainer'), ('one_time_payment', 'One time Payment')],
                                    default='is_retainer')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # is_notification_sent_to_account_manager = fields.Boolean(string="Is Notification Sent To Account Manager")

    def get_contract_duration(self):
        diff = relativedelta(self.end_date, self.start_date)
        if self.end_date and self.start_date:
            if diff.months == 0:
                return str(diff.days) + ' Days '
            else:
                return str(diff.months) + ' Months '
        else:
            return ""

    def action_quotation_send(self):
        action = super(SaleOrder, self).action_quotation_send()
        if self.opportunity_id and self.state in ['draft', 'quotation_submit', 'quotation_approved', 'sent']:
            context = action.get('context')
            template_id = self.env['ir.model.data'].xmlid_to_res_id(
                'qshield_crm.email_template_qshield_proposal_quotation',
                raise_if_not_found=False)
            context.update({'default_template_id': template_id})
            action.update({'context': context})
        return action

    @api.model
    def create(self, values):
        order = super(SaleOrder, self).create(values)
        if order.opportunity_id and not order.approver_setting_id:
            raise UserError('Please Configure Approval settings')
        if order.approver_setting_id and len(order.approver_ids) == 0:
            order.compute_approvers()
        return order

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_so_as_sent'):
            self.filtered(lambda o: o.state in ['draft', 'quotation_approved']).with_context(
                tracking_disable=True).write({'state': 'sent'})
            self.env.company.sudo().set_onboarding_step_done('sale_onboarding_sample_quotation_state')
        return super(SaleOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    @api.model
    def create_invoice_from_server_action(self):
        invoice_ids = []
        for order in self:
            invoice = order._create_invoices()
            if invoice:
                invoice_ids.append(invoice.id)
        return {
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', invoice_ids)],
        }

    @api.model
    def create_invoice_activity(self):
        sale_orders = self.env['sale.order'].search([])
        today = date.today()
        for order in sale_orders:
            if order.account_manager.user_id and (order.due_date and order.due_date == today):
                activity = self.env.ref('qshield_crm.mail_activity_data_sale_order').id
                due_date_activity = self.sudo()._get_user_approval_activities(user=self.env.user,
                                                                              activity_type_id=activity)
                if not due_date_activity:
                    order.activity_schedule(
                        'qshield_crm.mail_activity_due_date_sale_order',
                        user_id=order.account_manager.user_id.id)

    @api.depends('state', 'order_line.invoice_status')
    def _get_invoice_status(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state not in ['sale', 'done', 'submit_client_operation'])

        unconfirmed_orders.invoice_status = 'no'
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d['order_id'][0], d['invoice_status'])
            for d in self.env['sale.order.line'].read_group([
                ('order_id', 'in', confirmed_orders.ids),
                ('is_downpayment', '=', False),
                ('display_type', '=', False),
            ],
                ['order_id', 'invoice_status'],
                ['order_id', 'invoice_status'], lazy=False)]
        for order in confirmed_orders:
            line_invoice_status = [d[1] for d in line_invoice_status_all if d[0] == order.id]
            if order.state not in ('sale', 'done', 'submit_client_operation'):
                order.invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                order.invoice_status = 'to invoice'
            elif line_invoice_status and all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                order.invoice_status = 'invoiced'
            elif line_invoice_status and all(
                    invoice_status in ('invoiced', 'upselling') for invoice_status in line_invoice_status):
                order.invoice_status = 'upselling'
            else:
                order.invoice_status = 'no'

    @api.depends('opportunity_id')
    def compute_is_valid_for_agreement(self):
        for record in self:
            if record.opportunity_id.stage_id.is_won:
                record.is_valid_for_agreement = True
            else:
                record.is_valid_for_agreement = False

    @api.depends('approver_ids')
    def compute_is_approver_user(self):
        for record in self:
            if record.approver_ids:
                if record.approver_ids.filtered(lambda x: x.user_id == self.env.user) and record.opportunity_id:
                    record.is_approver_user = True
                else:
                    record.is_approver_user = False
            else:
                record.is_approver_user = False

    @api.depends('approver_ids')
    def _compute_user_status(self):
        for order in self:
            approvers = order.approver_ids.filtered(
                lambda approver: approver.user_id == self.env.user).filtered(
                lambda approver: approver.status != 'approved')
            if len(approvers) > 0:
                order.user_status = approvers[0].status
            else:
                order.user_status = False

    @api.depends('user_id')
    def compute_approver_settings_id(self):
        for rec in self:
            rec.approver_setting_id = self.env['sale.order.approver.settings'].search([], limit=1).id

    @api.onchange('approver_setting_id')
    def compute_approvers(self):
        current_users = self.approver_ids.mapped('user_id')
        new_users = self.approver_setting_id.approver_ids
        for user in new_users - current_users:
            record = self.env['sale.order.approver'].new({
                'user_id': user.id,
                'status': 'draft'})
            self.approver_ids += record

    def submit_quotation(self):
        for record in self:
            for approver in self.mapped('approver_ids').filtered(lambda approver: approver.status == 'refused'):
                approver.write({'status': 'draft'})
            approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'draft')
            if approvers:
                approvers[0]._create_activity()
                approvers[0].write({'status': 'pending'})
            activity = self.env.ref('qshield_crm.mail_activity_data_sale_order').id
            self.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
            record.write({'state': 'quotation_submit'})

    def _get_user_approval_activities(self, user, activity_type_id):
        domain = [
            ('res_model', '=', 'sale.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', activity_type_id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities

    def approve_quotation(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            ).filtered(
                lambda approver: approver.status != 'approved')
        if len(approver) > 0:
            approver[0].write({'status': 'approved', 'approval_date': datetime.now()})
        activity = self.env.ref('qshield_crm.mail_activity_data_sale_order').id
        self.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver[0].status == 'draft')
        if len(approvers) > 0:
            approvers[0]._create_activity()
            approvers[0].write({'status': 'pending'})
        else:
            product_ids = self.order_line.mapped('product_id').ids
            service_types = self.env['ebs_mod.service.types'].search([('product_id', 'in', product_ids)])
            start_date = datetime.strftime(self.start_date, '%Y-%m-%d')
            end_date = datetime.strftime(self.end_date, '%Y-%m-%d')
            contract = self.env['ebs_mod.contracts'].create({
                'name': 'Contract for sale order of ' + self.name,
                'start_date': start_date,
                'end_date': end_date,
                'contract_type': 'retainer_agreement',
                'service_ids': service_types.ids,
                'contact_id': self.partner_id.id
            })
            self.write({'state': 'quotation_approved'})

    def approve_agreement(self, approver=None):
        if not isinstance(approver, models.BaseModel):
            approver = self.mapped('approver_ids').filtered(
                lambda approver: approver.user_id == self.env.user
            ).filtered(
                lambda approver: approver.status != 'approved')
        if len(approver) > 0:
            approver[0].write({'status': 'approved', 'approval_date': datetime.now()})
        activity = self.env.ref('qshield_crm.mail_activity_data_sale_order').id
        self.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver[0].status == 'draft')
        if len(approvers) > 0:
            approvers[0]._create_activity()
            approvers[0].write({'status': 'pending'})
        else:
            self.write({'state': 'submit_client_operation'})

    def create_refuse_activity(self):
        for approver in self:
            approver.sale_order_id.activity_schedule(
                'qshield_crm.mail_activity_data_sale_order',
                user_id=approver.user_id.id)

    def submit_agreement(self):
        for approver in self.approver_ids:
            approver.write({'status': 'draft'})
        approvers = self.mapped('approver_ids').filtered(lambda approver: approver.status == 'draft')
        if approvers:
            approvers[0]._create_activity()
            approvers[0].write({'status': 'pending'})
        activity = self.env.ref('qshield_crm.mail_activity_data_sale_order').id
        self.sudo()._get_user_approval_activities(user=self.env.user, activity_type_id=activity).action_feedback()
        self.write({'state': 'agreement_submit'})

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.approver_ids:
            for approver in self.approver_ids:
                approver.write({'status': 'cancel'})
        return res

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        if self.approver_ids:
            for approver in self.approver_ids:
                approver.write({'status': 'draft'})
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if res:
            for rec in self:
                if rec.opportunity_id:
                    rec.opportunity_id.action_set_won_rainbowman()
                    msg = (_('Opportunity Won {}'.format(rec.opportunity_id.name)))
                    self.message_post(body=msg)
        return res

    def action_unlock(self):
        for rec in self:
            if rec.opportunity_id:
                rec.write({'state': 'submit_client_operation'})
            else:
                super(SaleOrder, rec).action_unlock()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_get_to_invoice_qty()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs onyl in state 'sale', so that when a SO is set to done, the upselling opportunity
          is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state not in ('sale', 'done', 'submit_client_operation'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and \
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done', 'submit_client_operation']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
