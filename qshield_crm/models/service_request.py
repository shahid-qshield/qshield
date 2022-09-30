# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import calendar
from datetime import datetime, date
from odoo.exceptions import ValidationError, UserError


class ServiceRequest(models.Model):
    _inherit = 'ebs_mod.service.request'

    def default_invoice_term_start_date(self):
        return date.today().replace(day=1)

    def default_invoice_term_end_date(self):
        today = date.today()
        days = calendar.monthrange(today.year, today.month)
        return today.replace(day=days[1])

    sale_order_id = fields.Many2one(comodel_name='sale.order', string="Sale Order", copy=False)
    partner_invoice_type = fields.Selection(related="partner_id.partner_invoice_type")
    invoice_term_start_date = fields.Date(string="Invoice Term Start Date", default=default_invoice_term_start_date)
    invoice_term_end_date = fields.Date(string="Invoice Term End Date", default=default_invoice_term_end_date)
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")
    is_in_scope = fields.Boolean("Is In of Scope", compute="compute_is_in_scope", store=True)
    is_end_date = fields.Boolean(string="Is End date", compute="compute_is_end_date")
    is_included_in_invoice = fields.Boolean(string="Is Included in invoice")

    def generate_invoice_base_on_service_end(self):
        if self.end_date:
            if self.is_in_scope and self.partner_invoice_type in ['retainer','outsourcing']:
                invoice_term = self.contract_id.sale_order_id.invoice_term_ids.filtered(
                    lambda s: s.start_term_date <= self.end_date.date() <= s.end_term_date)
                if invoice_term and not invoice_term.invoice_id:
                    if self.expenses_ids:
                        for expense in self.expenses_ids:
                            expense.sudo().write({'is_set_from_cron': True, 'invoice_date': self.end_date})
                    invoice_term.sudo().write({'due_date': self.end_date})
                    invoice_term.create_retainer_invoice()
                if invoice_term and invoice_term.invoice_id:
                    self.update_existing_invoice(invoice_term, invoice_term.invoice_id)
            elif self.is_out_of_scope and not self.is_one_time_transaction and self.sale_order_id:
                invoice_term = self.sale_order_id.invoice_term_ids.filtered(
                    lambda s: s.start_term_date <= self.end_date.date() <= s.end_term_date)
                if invoice_term:
                    if invoice_term[0].sale_id.state in ['sale', 'done', 'submit_client_operation']:
                        if self.expenses_ids:
                            for expense in self.expenses_ids:
                                expense.sudo().write({'is_set_from_cron': True, 'invoice_date': self.end_date})
                        invoice_term.sudo().write({'due_date': self.end_date})
                        invoice_term.create_retainer_invoice()
                    else:
                        raise UserError('Sale order flow is incomplete')
                else:
                    raise UserError('Invoice term for this service not created')
            elif self.is_one_time_transaction and self.sale_order_id:
                invoice_term = self.sale_order_id.invoice_term_ids
                if invoice_term:
                    if invoice_term[0].sale_id.state in ['sale', 'done', 'submit_client_operation']:
                        if self.expenses_ids:
                            for expense in self.expenses_ids:
                                expense.sudo().write({'is_set_from_cron': True, 'invoice_date': self.end_date})
                        invoice_term[0].sudo().write({'due_date': self.end_date})
                        invoice_term[0].create_retainer_invoice()
                    else:
                        raise UserError('Sale order flow is incomplete')
                else:
                    raise UserError('Invoice term for this service not created')

    def update_existing_invoice(self, invoice_term, invoice_id):
        invoice_line_without_government_fees = invoice_id.invoice_line_ids.filtered(
            lambda s: not s.is_government_fees_line)
        invoice_line_with_government_fees = invoice_id.invoice_line_ids.filtered(
            lambda s: s.is_government_fees_line)
        data = [{line.service_request_id: line.price_unit, 'name': line.name, 'product_id': line.product_id.id,
                 'description': line.description} for line in invoice_line_without_government_fees]
        old_service_requests = invoice_line_without_government_fees.mapped('service_request_id')
        old_service_requests = old_service_requests + invoice_line_with_government_fees.mapped(
            'service_request_id').filtered(lambda s: s not in old_service_requests)
        if self not in old_service_requests and self.is_in_scope:
            invoice_amount = invoice_term.amount / (len(old_service_requests.filtered(
                lambda s: s.is_in_scope and s.contract_id == self.contract_id)) + 1)
        else:
            invoice_amount = invoice_term.amount / (
                len(old_service_requests.filtered(lambda s: s.is_in_scope and s.contract_id == self.contract_id)))
        if invoice_id.sudo().line_ids:
            invoice_id.line_ids.sudo().unlink()
        if invoice_id.sudo().invoice_line_ids:
            invoice_id.sudo().invoice_line_ids.unlink()
        if self not in old_service_requests and self.is_in_scope:
            invoice_id.sudo().write({
                'invoice_line_ids': [(0, 0,
                                      {
                                          'product_id': self.service_type_id.variant_id.product_id.id,
                                          'name': self.service_type_id.variant_id.product_id.name,
                                          'quantity': 1,
                                          'price_unit': invoice_amount,
                                          'description': self.name,
                                          'service_request_id': self.id,
                                      })]
            })
            self.write({'is_included_in_invoice': True})
        if old_service_requests:
            for line in old_service_requests:
                product_id = line.service_type_id.variant_id.product_id.id
                name = line.service_type_id.variant_id.product_id.name
                description = line.name
                if not line.is_in_scope or (line.is_in_scope and line.contract_id != self.contract_id):
                    filter_data = list(filter(lambda s: s.get(line), data))
                    if filter_data:
                        invoice_amount = filter_data[0].get(line)
                        product_id = filter_data[0].get('product_id')
                        name = filter_data[0].get('name')
                        description = filter_data[0].get('description')

                invoice_id.sudo().write({
                    'invoice_line_ids': [(0, 0,
                                          {
                                              'product_id': product_id,
                                              'name': name,
                                              'quantity': 1,
                                              'price_unit': invoice_amount,
                                              'description': description,
                                              'service_request_id': line.id
                                          })]
                })
            if self.is_out_of_scope and not self.is_one_time_transaction:
                invoice_line_vals = invoice_term.get_invoice_line_base_on_invoice_term_of_down(invoice_term, [])
                if invoice_line_vals:
                    invoice_id.sudo().write({'invoice_line_ids': invoice_line_vals})
            expense_ids = old_service_requests.mapped('expenses_ids')
            if self not in old_service_requests:
                other_expenses = self.expenses_ids.filtered(lambda s: s not in expense_ids)
                expense_ids = expense_ids + other_expenses
                if other_expenses:
                    for expense in other_expenses:
                        if expense.attachment_ids:
                            for attachment_id in expense.attachment_ids:
                                self.env['ir.attachment'].sudo().create(
                                    {
                                        'name': attachment_id.name,
                                        'type': attachment_id.type,
                                        'datas': attachment_id.datas,
                                        'mimetype': attachment_id.mimetype,
                                        'res_model': invoice_id._name,
                                        'res_id': invoice_id.id,
                                        'res_name': invoice_id.name,
                                    }
                                )
            if expense_ids:
                for expense in expense_ids:
                    invoice_id.sudo().write({
                        'invoice_line_ids': [(0, 0,
                                              {
                                                  'product_id': expense.expense_type_id.product_id.id,
                                                  'name': expense.expense_type_id.product_id.name,
                                                  'quantity': 1,
                                                  'price_unit': expense.amount,
                                                  'description': expense.service_request_id.name,
                                                  'service_request_id': expense.service_request_id.id,
                                                  'is_government_fees_line': True
                                              })]
                    })
                    expense.sudo().write({'invoice_id': invoice_id.id})
        else:
            for expense in self.expenses_ids:
                invoice_id.sudo().write({
                    'invoice_line_ids': [(0, 0,
                                          {
                                              'product_id': expense.expense_type_id.product_id.id,
                                              'name': expense.expense_type_id.product_id.name,
                                              'quantity': 1,
                                              'price_unit': expense.amount,
                                              'description': self.name,
                                              'service_request_id': self.id,
                                              'is_government_fees_line': True
                                          })]
                })
                expense.sudo().write({'invoice_id': invoice_id.id})
                if expense.attachment_ids:
                    for attachment_id in expense.attachment_ids:
                        self.env['ir.attachment'].sudo().create(
                            {
                                'name': attachment_id.name,
                                'type': attachment_id.type,
                                'datas': attachment_id.datas,
                                'mimetype': attachment_id.mimetype,
                                'res_model': invoice_id._name,
                                'res_id': invoice_id.id,
                                'res_name': invoice_id.name,
                            }
                        )

    @api.depends('end_date')
    def compute_is_end_date(self):
        for record in self:
            if record.end_date and record.partner_invoice_type in ['per_transaction',
                                                                   'partners'] and record.sale_order_id:
                if record.sale_order_id.invoice_term_ids:
                    for invoice_term in record.sale_order_id.invoice_term_ids:
                        invoice_term.due_date = record.end_date.date()
            elif record.end_date and record.is_one_time_transaction and record.sale_order_id and record.sale_order_id.invoice_term_ids:
                for invoice_term in record.sale_order_id.invoice_term_ids:
                    invoice_term.due_date = record.end_date.date()
            record.is_end_date = True

        # elif self.end_date and self.partner_invoice_type == 'one_time_transaction' and self.sale_order_id:
        #     if self.sale_order_id.invoice_term_ids:
        #         for record in self.sale_order_id.invoice_term_ids:
        #             record.due_date = self.end_date.date()
        #     else:
        #         self.sale_order_id.

    @api.onchange('partner_id', 'service_type_id')
    def onchange_partner_partner_invoice_type(self):
        if self.partner_id and self.partner_id.partner_invoice_type in ['per_transaction', 'one_time_transaction',
                                                                        'partners']:
            self.is_one_time_transaction = True
        else:
            self.is_one_time_transaction = False

    @api.depends('service_type_id', 'contract_id')
    def compute_is_in_scope(self):
        for record in self:
            is_in_scope = False
            if record.service_type_id and record.contract_id:
                in_scope_service = record.contract_id.sudo().service_ids.filtered(
                    lambda s: s in record.service_type_id)
                if in_scope_service:
                    record.is_one_time_transaction = False
                    is_in_scope = True
            if record.partner_id and not record.contract_id and record.partner_id.partner_invoice_type in [
                'per_transaction',
                'one_time_transaction',
                'partners']:
                record.is_one_time_transaction = True

            record.is_in_scope = is_in_scope

    @api.onchange('partner_id')
    def onchange_partner_id_custom(self):
        if self.partner_id and self.partner_id.partner_invoice_type and self.partner_id.partner_invoice_type not in [
            'retainer', 'outsourcing']:
            self.is_one_time_transaction = True

    @api.model
    def create(self, values):
        res = super(ServiceRequest, self).create(values)
        if len(res.service_flow_ids) == 0:
            raise ValidationError(_("Missing Workflow!"))
        if res.partner_invoice_type in ['partners', 'per_transaction']:
            res.generate_sale_order()
        return res

    def generate_sale_order(self):
        if self.is_out_of_scope or self.is_one_time_transaction:
            order_id = self.env['sale.order'].sudo().create({
                'partner_id': self.partner_id.id,
                'account_manager': self.partner_id.account_manager.id if self.partner_id.account_manager else False,
                'is_out_of_scope': True,
                'generate_order_line': 'from_consolidation',
                'is_agreement': 'one_time_payment' if self.is_one_time_transaction else 'is_retainer',
                # 'order_line': [(0, 0, {
                #     'product_id': self.service_type_id.variant_id.product_id.id,
                #     'name': self.service_type_id.variant_id.product_id.name,
                #     'product_uom_qty': 1,
                #     'price_unit': self.service_type_id.variant_id.product_id.lst_price,
                # })]
            })
            if order_id:
                self.write({'sale_order_id': order_id.id})
                order_id.sudo().write({'order_line': [(0, 0, {
                    'display_type': 'line_section',
                    'name': self.service_type_id and self.service_type_id.variant_id and self.service_type_id.variant_id.consolidation_id.name
                })]})
                order_id.sudo().write({'order_line': [(0, 0, {
                    'product_id': self.service_type_id.variant_id.product_id.id,
                    'name': self.service_type_id.variant_id.product_id.name,
                    'product_uom_qty': 1,
                    'price_unit': self.service_type_id.variant_id.product_id.lst_price,
                })]})
                if self.partner_invoice_type in ['partners', 'per_transaction']:
                    payment_term_id = self.env.ref('account.account_payment_term_immediate').id
                    approvers = order_id.mapped('approver_ids').filtered(
                        lambda approver: approver.status != 'approved')
                    if len(approvers) > 0:
                        for approver in approvers:
                            approver.sudo().write({'status': 'approved', 'approval_date': datetime.now()})
                    order_id.sudo().write({'state': 'sale', 'payment_term_id': payment_term_id})
                    if order_id.opportunity_id:
                        order_id.sudo().write({'state': 'submit_client_operation'})
                        order_id.opportunity_id.action_set_won_rainbowman()
                        msg = (_('Opportunity Won {}'.format(order_id.opportunity_id.name)))
                        order_id.message_post(body=msg)
                    self.request_submit()
                    if self.invoice_term_start_date and self.invoice_term_end_date:
                        order_id.sudo().write(
                            {'start_date': self.invoice_term_start_date, 'end_date': self.invoice_term_end_date})
                        order_id.sudo().action_create_invoice_term()


class EbsModContracts(models.Model):
    _inherit = 'ebs_mod.contracts'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string="Sale Order", track_visibility='onchange')
    no_of_employees = fields.Integer(string="No Of Employees")


class ExpenseTypes(models.Model):
    _inherit = 'ebs_mod.expense.types'

    product_id = fields.Many2one('product.product', string="Product")
    type = fields.Selection([('government', 'Government'),
                             ('other', 'Other')], string="Type")


class EbsModServiceRequestExpenses(models.Model):
    _inherit = 'ebs_mod.service.request.expenses'

    made_by = fields.Text(string="Made by")
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment')
    invoice_id = fields.Many2one('account.move', string="Related Invoice")
    to_invoice = fields.Boolean(string="To Invoice", compute="compute_to_invoice")
    invoice_date = fields.Date(string="Invoice Date")
    invoice_due_date = fields.Date(string="Invoice Due Date", compute="compute_invoice_due_date", store=True)
    is_set_res_id_in_attachment = fields.Boolean(compute="compute_is_set_res_id_in_attachment")
    is_set_from_cron = fields.Boolean(string="IS set from cron")

    @api.onchange('date')
    def onchange_invoice_date(self):
        if self.date:
            self.invoice_date = self.date

    @api.depends()
    def compute_is_set_res_id_in_attachment(self):
        for record in self:
            if record.attachment_ids:
                for attachment_id in record.attachment_ids:
                    attachment_id.sudo().write({'res_id': record.id})
            record.is_set_res_id_in_attachment = True

    @api.depends('invoice_date')
    def compute_invoice_due_date(self):
        for record in self:
            if record.invoice_date and not record.is_set_from_cron:
                last_day_of_month = calendar.monthrange(record.invoice_date.year, record.invoice_date.month)[1]
                record.invoice_due_date = record.invoice_date.replace(day=last_day_of_month)
            elif record.is_set_from_cron and record.invoice_date:
                record.invoice_due_date = record.invoice_date
            else:
                record.invoice_due_date = False

    def compute_to_invoice(self):
        for rec in self:
            if not rec.invoice_id:
                rec.to_invoice = True
            else:
                rec.to_invoice = False
