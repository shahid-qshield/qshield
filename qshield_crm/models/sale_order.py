# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.tools import float_is_zero, float_compare
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import calendar


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def default_start_date(self):
        return date.today().replace(day=1)

    def default_end_date(self):
        today = date.today()
        days = calendar.monthrange(today.year, today.month)
        return today.replace(day=days[1])

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Agreement Submitted '),
        ('submit_client_operation', 'Submit Client To operation'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    qshield_crm_state = fields.Selection(related="state")
    qshield_service_state = fields.Selection(related="state")
    account_manager = fields.Many2one('hr.employee', string="Account Manager")
    due_date = fields.Date(string="Due Date")
    refuse_quotation_reason = fields.Text(string="Refuse Quotation Reason")
    refuse_agreement_reason = fields.Text(string="Refuse Agreement Reason")
    is_valid_for_agreement = fields.Boolean(compute='compute_is_valid_for_agreement')
    invoice_term_ids = fields.One2many('invoice.term.line', 'sale_id', 'Invoicing Terms')
    is_agreement = fields.Selection([('is_retainer', 'Is Retainer'), ('one_time_payment', 'One time Payment')],
                                    default='is_retainer')
    start_date = fields.Date(string="Start Date", default=default_start_date)
    end_date = fields.Date(string="End Date", default=default_end_date)
    generate_order_line = fields.Selection([('from_consolidation', 'From Consolidation'), ('manual', 'Manual')],
                                           default='manual')
    is_out_of_scope = fields.Boolean(string="Is out of scope")
    no_of_employees = fields.Integer(string="Number of Employees")
    is_invoice_term_created = fields.Boolean(string="Is Invoice Term Created",
                                             compute="_compute_is_invoice_term_created")
    partner_invoice_type = fields.Selection(related="partner_id.partner_invoice_type")

    # is_notification_sent_to_account_manager = fields.Boolean(string="Is Notification Sent To Account Manager")
    def close_quotation_activity(self):
        activity = self.env.ref('qshield_crm.mail_activity_quotation').id
        domain = [
            ('res_model', '=', 'sale.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', activity)
        ]
        self.env['mail.activity'].search(domain).action_feedback()

    @api.onchange('partner_id')
    def onchange_partner_id_custom_method(self):
        if self.partner_id and self.partner_id.account_manager:
            self.account_manager = self.partner_id.account_manager.id

    @api.depends('invoice_term_ids')
    def _compute_is_invoice_term_created(self):
        for rec in self:
            rec.is_invoice_term_created = True if rec.invoice_term_ids else False

    def action_generate_sale_order_line(self):
        if self.id:
            generate_sale_order_line = self.env['generate.sale.order.line'].sudo().search(
                [('sale_order_id', '=', self.id)], limit=1)
            if not generate_sale_order_line:
                generate_sale_order_line = self.env['generate.sale.order.line'].sudo().create(
                    {'sale_order_id': self.id})
            action = self.env.ref('qshield_crm.action_generate_sale_order_line').read()[0]
            action.update({'res_id': generate_sale_order_line.id})
            return action

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
        if self.opportunity_id and self.state in ['draft', 'sent']:
            context = action.get('context')
            template_id = self.env['ir.model.data'].xmlid_to_res_id(
                'qshield_crm.email_template_qshield_proposal_quotation',
                raise_if_not_found=False)

            context.update({'default_template_id': template_id})
            action.update({'context': context})
        if self.is_out_of_scope:
            context = action.get('context')
            # template_id = self.env['ir.model.data'].xmlid_to_res_id(
            #     'qshield_crm.email_template_of_send_notification_to_client',
            #     raise_if_not_found=False)
            template_id = self.env.ref('qshield_crm.email_template_of_send_notification_to_client')
            context.update({'default_template_id': template_id.id})
            action.update({'context': context})
        return action

    def action_quotation_sent(self):
        res = super().action_quotation_sent()
        self.write({'state': 'draft'})
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        res = super(models.Model, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)
        if self.env.context.get('mark_so_as_sent'):
            self.env.company.sudo().set_onboarding_step_done('sale_onboarding_sample_quotation_state')
        return res

    def action_create_invoice_term(self):
        if self.invoice_term_ids:
            self.sudo().invoice_term_ids.unlink()
        if self.is_agreement == 'is_retainer':
            # num_months = (self.end_date.year - self.start_date.year) * 12 + (
            #         self.end_date.month - self.start_date.month) + 1
            # if num_months == 0:
            #     num_months = 1
            for first_day_date in self.months_between(self.end_date, self.start_date):
                if first_day_date:
                    last_day_of_month = calendar.monthrange(first_day_date.year, first_day_date.month)[1]
                    last_day_date = first_day_date.replace(day=last_day_of_month)
                    self.env['invoice.term.line'].sudo().create({
                        'name': first_day_date.strftime('%b') + ' ' + first_day_date.strftime('%Y') + ' - invoice term',
                        'start_term_date': first_day_date,
                        'end_term_date': last_day_date,
                        'due_date': last_day_date,
                        'type': 'down',
                        'invoice_amount_type': 'amount',
                        'amount': self.amount_total,
                        'sale_id': self.id
                    })
            if self.is_out_of_scope:
                self.create_agreement_of_customer()
        elif self.is_agreement == 'one_time_payment':
            last_day_of_month = calendar.monthrange(self.end_date.year, self.end_date.month)[1]
            last_day_date = self.end_date.replace(day=last_day_of_month)
            self.env['invoice.term.line'].sudo().create({
                'name': self.start_date.strftime('%b') + ' ' + self.start_date.strftime('%Y') + ' - invoice term',
                'start_term_date': self.start_date,
                'end_term_date': self.end_date,
                'due_date': last_day_date,
                'type': 'regular_invoice',
                'invoice_amount_type': 'amount',
                'amount': self.amount_total,
                'sale_id': self.id
            })
        return True

    # def action_done(self):
    #     res = super(SaleOrder, self).action_done()
    #     if self.is_agreement == 'is_retainer':
    #         for first_day_date in self.months_between(self.end_date, self.start_date):
    #             if first_day_date:
    #                 last_day_of_month = calendar.monthrange(first_day_date.year, first_day_date.month)[1]
    #                 last_day_date = first_day_date.replace(day=last_day_of_month)
    #                 self.env['invoice.term.line'].sudo().create({
    #                     'name': first_day_date.strftime('%b') + ' ' + first_day_date.strftime('%Y') + ' - invoice term',
    #                     'start_term_date': first_day_date,
    #                     'end_term_date': last_day_date,
    #                     'due_date': last_day_date,
    #                     'type': 'down',
    #                     'invoice_amount_type': 'amount',
    #                     'amount': self.amount_total,
    #                     'sale_id': self.id
    #                 })
    #         if self.is_out_of_scope:
    #             self.create_agreement_of_customer()
    #     elif self.is_agreement == 'one_time_payment':
    #         self.env['invoice.term.line'].sudo().create({
    #             'name': self.start_date.strftime('%b') + ' ' + self.start_date.strftime('%Y') + ' - invoice term',
    #             'start_term_date': self.start_date,
    #             'end_term_date': self.end_date,
    #             'due_date': self.end_date,
    #             'type': 'regular_invoice',
    #             'invoice_amount_type': 'amount',
    #             'amount': self.amount_total,
    #             'sale_id': self.id
    #         })
    #     return res

    def months_between(self, end_date, start_date):
        if start_date > end_date:
            month = False
            yield month
        else:
            year = start_date.year
            month = start_date.month
            while (year, month) <= (end_date.year, end_date.month):
                yield date(year, month, 1)
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1

    @api.model
    def create(self, values):
        order = super(SaleOrder, self).create(values)
        if order.opportunity_id:
            order.get_amount_of_linked_so_with_opportunity()
        return order

    def write(self, values):
        res = super(SaleOrder, self).write(values)
        if self.opportunity_id:
            self.get_amount_of_linked_so_with_opportunity()
        return res

    def get_amount_of_linked_so_with_opportunity(self):
        for order in self:
            orders = self.search([('state', '!=', 'cancel'), ('opportunity_id', '=', order.opportunity_id.id)])
            total_amount = sum(orders.mapped('amount_total'))
            self.opportunity_id.sudo().write({'planned_revenue': total_amount})

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

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

    def _get_user_approval_activities(self, user, activity_type_id):
        domain = [
            ('res_model', '=', 'sale.order'),
            ('res_id', 'in', self.ids),
            ('activity_type_id', '=', activity_type_id),
            ('user_id', '=', user.id)
        ]
        activities = self.env['mail.activity'].search(domain)
        return activities

    def approve_agreement(self, approver=None):
        template = self.env.ref(
            'qshield_crm.email_template_quotation_submit_to_client',
            raise_if_not_found=False)
        self.send_notification(template)
        self.write({'state': 'submit_client_operation'})
        if self.partner_invoice_type in ['retainer', 'outsourcing']:
            self.create_agreement_of_customer()

    def create_refuse_activity(self):
        for approver in self:
            approver.sale_order_id.activity_schedule(
                'qshield_crm.mail_activity_data_sale_order',
                user_id=approver.user_id.id)

    def create_agreement_of_customer(self):
        product_ids = self.order_line.mapped('product_id').ids
        # service_variants = self.env['ebs_mod.service.type.variants'].sudo().search(
        #     [('product_id', 'in', product_ids)])
        # service_types = service_variants.mapped('service_type')
        service_types = self.env['ebs_mod.service.types'].sudo().search([('product_id', 'in', product_ids)])
        start_date = datetime.strftime(self.start_date, '%Y-%m-%d')
        end_date = datetime.strftime(self.end_date, '%Y-%m-%d')
        contract = self.env['ebs_mod.contracts'].search(
            [('start_date', '=', start_date), ('end_date', '=', end_date), ('contact_id', '=', self.partner_id.id),
             ('sale_order_id', '=', self.id)])
        if not contract:
            contract = self.env['ebs_mod.contracts'].create({
                'name': 'Contract for sale order of ' + self.name,
                'start_date': start_date,
                'end_date': end_date,
                'contract_type': 'retainer_agreement',
                'service_ids': service_types.ids,
                'contact_id': self.partner_id.parent_company_id.id if self.partner_id.parent_company_id else self.partner_id.id,
                'sale_order_id': self.id,
                'no_of_employees': self.no_of_employees,
                # 'generated_by_sale_order': True,
            })
        else:
            contract.write({
                'name': 'Contract for sale order of ' + self.name,
                'start_date': start_date,
                'end_date': end_date,
                'contract_type': 'retainer_agreement',
                'service_ids': service_types.ids,
                'contact_id': self.partner_id.id,
                'sale_order_id': self.id,
                'no_of_employees': self.no_of_employees,
                # 'generated_by_sale_order': True,
            })

    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        if self.is_out_of_scope:
            template = self.env.ref(
                'qshield_crm.email_template_service_quotation_reject',
                raise_if_not_found=False)
            self.send_notification(template)
        return res

    def action_draft(self):
        res = super(SaleOrder, self).action_draft()
        for record in self:
            if record.invoice_term_ids:
                record.invoice_term_ids.sudo().unlink()
            service_request = self.env['ebs_mod.service.request'].sudo().search([('sale_order_id', '=', record.id)])
            if service_request:
                service_request.sudo().write({'status': 'draft'})
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if res:
            for rec in self:
                if rec.opportunity_id:
                    rec.opportunity_id.action_set_won_rainbowman()
                    msg = (_('Opportunity Won {}'.format(rec.opportunity_id.name)))
                    self.message_post(body=msg)
                if rec.is_out_of_scope:
                    template = self.env.ref(
                        'qshield_crm.email_template_service_quotation_approve',
                        raise_if_not_found=False)
                    service = rec.send_notification(template)
                    if service and service.status == 'draft':
                        service.sudo().request_submit()
            # self.close_quotation_activity()
        return res

    def send_notification(self, template):
        # partner_to = self.approver_setting_id.service_approver_notification_email
        partner_to = False
        if self.account_manager and self.account_manager.work_email:
            partner_to = self.account_manager.work_email
        service = self.env['ebs_mod.service.request'].sudo().search([('sale_order_id', '=', self.id)], limit=1)
        if service and service.partner_id and service.partner_id.email:
            if partner_to:
                partner_to = partner_to + ',' + service.partner_id.email
            else:
                partner_to = service.partner_id.email
        if partner_to and template:
            email_list = partner_to.split(',')
            email_from = self.env['ir.mail_server'].sudo().search([('smtp_user', '!=', False)], limit=1).smtp_user
            if not email_from:
                email_from = self.env.company.partner_id.email
            for email in email_list:
                template.sudo().with_context(
                    email_to=email, email_from=email_from).send_mail(self.id,
                                                                     force_send=True)
        return service or False

    def action_unlock(self):
        for rec in self:
            if rec.invoice_term_ids.filtered(lambda s: s.invoice_id):
                raise UserError('Please delete the related invoice first')
            else:
                rec.invoice_term_ids.sudo().unlink()
            if rec.opportunity_id:
                rec.write({'state': 'submit_client_operation'})
                # rec.write({'invoice_term_ids': False})
            else:
                super(SaleOrder, rec).action_unlock()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_unit = fields.Float('Unit Price', required=True, default=0.0, digits=(12, 8))
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', readonly=True, store=True)

    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.with_context(custom_context=True).compute_all(price, line.order_id.currency_id,
                                                                              line.product_uom_qty,
                                                                              product=line.product_id,
                                                                              partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups(
                    'account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

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
