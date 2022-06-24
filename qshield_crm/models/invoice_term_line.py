# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import calendar
import time


class InvoiceTermLine(models.Model):
    _name = 'invoice.term.line'
    _description = 'Invoice Term Line'

    name = fields.Char('Invoice Term')
    type = fields.Selection([('down', 'Down Payment'),
                             ('regular_invoice', 'Regular Invoice'),
                             ('regular_invoice_with_deduct', 'Regular invoice with Deduct down payments')], 'Type',
                            default='down')
    invoice_amount_type = fields.Selection([('percentage', 'Percentage'), ('amount', 'Amount')], default='percentage',
                                           string="Amount Type")
    percentage = fields.Float('Percentage %')
    amount = fields.Float('Amount')
    sale_id = fields.Many2one('sale.order', string='Order Reference')
    invoice_id = fields.Many2one('account.move', string="Related Invoice")
    to_invoice = fields.Boolean(string="To Invoice", compute="compute_to_invoice")
    start_term_date = fields.Date(string="Start Date")
    end_term_date = fields.Date(string="End Date")
    due_date = fields.Date(string="Due Date")

    def compute_to_invoice(self):
        for rec in self:
            if not rec.invoice_id:
                rec.to_invoice = True
            else:
                rec.to_invoice = False

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.product_id.property_account_income_id.id,
            'taxes_id': [(6, 0, self.product_id.taxes_id.ids)],
            'company_id': False,
        }

    def _get_advance_details(self, invoice_term, order, product_id):
        if invoice_term.percentage > 0:
            if all(product_id.taxes_id.mapped('price_include')):
                amount = order.amount_total * invoice_term.percentage / 100
            else:
                amount = order.amount_untaxed * invoice_term.percentage / 100
            name = _("Down payment of %s%%") % (invoice_term.percentage)
        elif invoice_term.amount > 0:
            amount = invoice_term.amount
            name = _("Down payment")
        return amount, name

    def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount, product_id):
        context = {'lang': order.partner_id.lang}
        so_values = {
            'name': _('Down Payment: %s') % (time.strftime('%m %Y'),),
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'order_id': order.id,
            'discount': 0.0,
            'product_uom': product_id.uom_id.id,
            'product_id': product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'tax_id': [(6, 0, tax_ids)],
            'is_downpayment': True,
        }
        del context
        return so_values

    def create_retainer_invoice(self):
        first_day_month = datetime.date.today().replace(day=1)
        last_no_day = calendar.monthrange(datetime.date.today().year, datetime.date.today().month)[1]
        last_day_month = datetime.date.today().replace(day=last_no_day)
        action = self.env.ref('qshield_crm.action_move_out_invoice_type_custom_action')
        # invoice_term_ids = self.sudo().search([('invoice_id', '=', False),('due_date', '<=', datetime.date.today())])
        invoice_term_ids = self.sudo().search(
            [('invoice_id', '=', False), ('due_date', '>=', first_day_month), ('due_date', '<=', last_day_month)])
        expenses_ids = self.env['ebs_mod.service.request.expenses'].sudo().search(
            [('invoice_id', '=', False), ('date', '>=', first_day_month), ('date', '<=', last_day_month)])
        service_request_ids = expenses_ids.mapped('service_request_id')
        sale_orders = invoice_term_ids.mapped('sale_id')
        partners = invoice_term_ids.mapped('sale_id').mapped('partner_id')
        for partner in partners:
            partner_sale_orders = sale_orders.filtered(lambda s: s.partner_id == partner)
            partner_invoice_term_ids = partner_sale_orders.mapped('invoice_term_ids').filtered(
                lambda s: s.id in invoice_term_ids.ids)
            partner_service_request_ids = service_request_ids.filtered(lambda s: s.partner_id == partner)
            invoice_vals = {
                'type': 'out_invoice',
                'partner_id': partner.id,
                'currency_id': partner.currency_id.id if partner.currency_id else self.env.company.currency_id.id,
                'invoice_date': datetime.date.today()
            }
            invoice_line_vals = []
            for invoice_term in partner_invoice_term_ids:
                if invoice_term.type == 'down':
                    product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
                    if product_id:
                        product_id = self.env['product.product'].sudo().browse(int(product_id))
                    if not product_id:
                        vals = {
                            'name': 'Down payment',
                            'type': 'service',
                            'invoice_policy': 'order',
                            'company_id': False,
                        }
                        product_id = self.env['product.product'].sudo().create(vals)
                        self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id',
                                                                         product_id.id)
                    amount, name = self._get_advance_details(invoice_term, invoice_term.sale_id, product_id)
                    if product_id.invoice_policy != 'order':
                        raise UserError(
                            _('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                    if product_id.type != 'service':
                        raise UserError(
                            _("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                    taxes = product_id.taxes_id.filtered(
                        lambda
                            r: not invoice_term.sale_id.company_id or r.company_id == invoice_term.sale_id.company_id)
                    if invoice_term.sale_id.fiscal_position_id and taxes:
                        tax_ids = invoice_term.sale_id.fiscal_position_id.map_tax(taxes, product_id,
                                                                                  invoice_term.sale_id.partner_shipping_id).ids
                    else:
                        tax_ids = taxes.ids
                    analytic_tag_ids = []
                    for line in invoice_term.sale_id.order_line:
                        analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                    so_line_values = self._prepare_so_line(invoice_term.sale_id, analytic_tag_ids, tax_ids, amount,
                                                           product_id)
                    so_line = self.env['sale.order.line'].create(so_line_values)
                    invoice_line_vals.append((0, 0, {
                        'name': name,
                        'price_unit': amount,
                        'quantity': 1.0,
                        'product_id': product_id.id,
                        'product_uom_id': so_line.product_uom.id,
                        'tax_ids': [(6, 0, so_line.tax_id.ids)],
                        'sale_line_ids': [(6, 0, [so_line.id])],
                        'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                        'analytic_account_id': invoice_term.sale_id.analytic_account_id.id or False,
                    }))
                elif invoice_term.type == 'regular_invoice':
                    invoiceable_lines = invoice_term.sale_id._get_invoiceable_lines(final=True)
                    if not invoiceable_lines:
                        raise UserError(
                            _('There is no invoiceable line. If a product has a Delivered quantities invoicing policy, please make sure that a quantity has been delivered.'))
                    # invoice_line_vals.append((0, 0, line._prepare_invoice_line())
                    #                          for line in invoiceable_lines)
                    if invoiceable_lines:
                        for line in invoiceable_lines:
                            if line.product_id:
                                vals = line._prepare_invoice_line()
                                if vals:
                                    invoice_line_vals.append((0, 0, vals))
            for expenses_id in expenses_ids.filtered(lambda s: s.service_request_id in partner_service_request_ids):
                invoice_line_vals.append((0, 0, {
                    'product_id': expenses_id.expense_type_id.product_id.id,
                    'name': expenses_id.desc if expenses_id.desc else expenses_id.expense_type_id.product_id.name,
                    'quantity': 1,
                    'price_unit': expenses_id.amount if expenses_id.amount else
                    expenses_id.expense_type_id.product_id.lst_price,
                    'service_request_id': expenses_id.service_request_id.id
                }))

            if invoice_line_vals:
                invoice_vals.update({'invoice_line_ids': invoice_line_vals})
            invoice_id = self.env['account.move'].sudo().create(invoice_vals)
            if invoice_id:
                if partner_invoice_term_ids:
                    partner_invoice_term_ids.write({'invoice_id': invoice_id.id})
                partner_expense_ids = expenses_ids.filtered(
                    lambda s: s.service_request_id in partner_service_request_ids)
                if partner_expense_ids:
                    partner_expense_ids.write({'invoice_id': invoice_id.id})
                    partner_attachment_ids = partner_expense_ids.mapped('attachment_ids')
                    if partner_attachment_ids:
                        for attachment_id in partner_attachment_ids:
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
                #
                # if invoice_id.sale_id.is_agreement == 'is_retainer' and invoice_id.sale_id.is_out_of_scope:
                #     invoice_id.sudo().write({'qshield_invoice_type': 'out_of_scope_retainer'})
                #
                # elif invoice_id.sale_id.is_agreement == 'is_retainer' and not invoice_id.sale_id.is_out_of_scope:
                #     invoice_id.sudo().write({'qshield_invoice_type': 'retainer'})
                # elif invoice_id.sale_id.is_agreement == 'one_time_payment' and invoice_id.sale_id.is_out_of_scope:
                #     invoice_id.sudo().write({'qshield_invoice_type': 'out_of_scope_one_time_payment'})
                # else:
                #     invoice_id.sudo().write({'qshield_invoice_type': 'one_time_payment'})
                get_url = str(self.env['ir.config_parameter'].sudo().search(
                    [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
                    invoice_id.id) + '&view_type=form&model=account.move&action=' + str(
                    action.id) + ' & menu_id = '
                prepared_url = '<a href="' + get_url + '" class="btn btn-primary">' + 'View Invoice' + '</a>'
                template = self.env.ref(
                    'qshield_crm.email_template_of_create_retainer_invoice',
                    raise_if_not_found=False)

                finance_user_ids = invoice_id.sale_id.approver_setting_id.finance_user_ids
                if not finance_user_ids:
                    approver_setting_id = self.env['sale.order.approver.settings'].sudo().search(
                        [('finance_user_ids', '!=', False)], limit=1)
                    finance_user_ids = approver_setting_id.finance_user_ids
                partner_to = [str(user.partner_id.id) for user in finance_user_ids if finance_user_ids]
                if partner_to:
                    template.sudo().with_context(
                        partner_to=','.join(partner_to), email_from=self.env.user.email,
                        link=prepared_url).send_mail(
                        invoice_id.id, force_send=True)
                for finance_user_id in finance_user_ids:
                    invoice_id.activity_schedule(
                        'qshield_crm.mail_activity_generated_invoice',
                        user_id=finance_user_id.id)

        # def create_retainer_invoice(self):
        first_day_month = datetime.date.today().replace(day=1)
        # last_no_day = calendar.monthrange(datetime.date.today().month, datetime.date.today().year)
        # last_day_month = datetime.date.today().replace(day=last_no_day)
        # invoice_term_ids = self.sudo().search([('invoice_id', '=', False),('due_date', '<=', datetime.date.today())])
        # invoice_term_ids = self.sudo().search(
        #     [('invoice_id', '=', False), ('due_date', '<=', first_day_month), ('due_date', '<=', last_day_month)])
        # sale_orders = invoice_term_ids.mapped('sale_id')
        # partners = invoice_term_ids.mapped('sale_id').mapped('partner_id')
        # action = self.env.ref('qshield_crm.action_move_out_invoice_type_custom_action')
    #     if invoice_term_ids:
    #         wizard_rec = self.env['create.multiple.invoice'].create({
    #             'invoice_term_ids': [(6, 0, invoice_term_ids.ids)]
    #         })
    #         if wizard_rec:
    #             invoice_ids = wizard_rec.create_invoices()
    #             if invoice_ids:
    #                 for invoice_id in invoice_ids:
    #                     if invoice_id.sale_id.is_agreement == 'is_retainer' and invoice_id.sale_id.is_out_of_scope:
    #                         invoice_id.sudo().write({'qshield_invoice_type': 'out_of_scope_retainer'})
    #
    #                     elif invoice_id.sale_id.is_agreement == 'is_retainer' and not invoice_id.sale_id.is_out_of_scope:
    #                         invoice_id.sudo().write({'qshield_invoice_type': 'retainer'})
    #                     elif invoice_id.sale_id.is_agreement == 'one_time_payment' and invoice_id.sale_id.is_out_of_scope:
    #                         invoice_id.sudo().write({'qshield_invoice_type': 'out_of_scope_one_time_payment'})
    #                     else:
    #                         invoice_id.sudo().write({'qshield_invoice_type': 'one_time_payment'})
    #                     get_url = str(self.env['ir.config_parameter'].sudo().search(
    #                         [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
    #                         invoice_id.id) + '&view_type=form&model=account.move&action=' + str(
    #                         action.id) + ' & menu_id = '
    #                     prepared_url = '<a href="' + get_url + '" class="btn btn-primary">' + 'View Invoice' + '</a>'
    #                     template = self.env.ref(
    #                         'qshield_crm.email_template_of_create_retainer_invoice',
    #                         raise_if_not_found=False)
    #
    #                     finance_user_ids = invoice_id.sale_id.approver_setting_id.finance_user_ids
    #                     if not finance_user_ids:
    #                         approver_setting_id = self.env['sale.order.approver.settings'].sudo().search(
    #                             [('finance_user_ids', '!=', False)], limit=1)
    #                         finance_user_ids = approver_setting_id.finance_user_ids
    #                     partner_to = [str(user.partner_id.id) for user in finance_user_ids if finance_user_ids]
    #                     if partner_to:
    #                         template.sudo().with_context(
    #                             partner_to=','.join(partner_to), email_from=self.env.user.email,
    #                             link=prepared_url).send_mail(
    #                             invoice_id.id, force_send=True)
    #                     for finance_user_id in finance_user_ids:
    #                         invoice_id.activity_schedule(
    #                             'qshield_crm.mail_activity_generated_invoice',
    #                             user_id=finance_user_id.id)
    #     expenses_ids = self.env['ebs_mod.service.request.expenses'].sudo().search(
    #         [('invoice_id', '=', False), ('date', '<=', datetime.date.today())])
    #     partner_ids = expenses_ids.mapped('service_request_id').mapped('partner_id')
    #     for partner_id in partner_ids:
    #         if not partner_id.property_account_receivable_id or not partner_id.property_account_payable_id:
    #             continue
    #         invoice = self.env['account.move'].with_context(default_type='out_invoice').create({
    #             'type': 'out_invoice',
    #             'partner_id': partner_id.id,
    #             'currency_id': partner_id.currency_id.id if partner_id.currency_id else self.env.company.currency_id.id,
    #             'invoice_date': datetime.date.today(),
    #             'qshield_invoice_type': 'expense_invoice'
    #         })
    #         # invoice_line_vals = []
    #         if expenses_ids and invoice:
    #             for expenses_id in expenses_ids:
    #                 if expenses_id.service_request_id.partner_id == partner_id:
    #                     invoice.sudo().write({'invoice_line_ids': [(0, 0, {
    #                         'product_id': expenses_id.expense_type_id.product_id.id,
    #                         'name': expenses_id.desc if expenses_id.desc else expenses_id.expense_type_id.product_id.name,
    #                         'quantity': 1,
    #                         'price_unit': expenses_id.amount if expenses_id.amount else
    #                         expenses_id.expense_type_id.product_id.lst_price,
    #                         'service_request_id': expenses_id.service_request_id.id
    #                     })]
    #                                           })
    #                     expenses_id.sudo().write({'invoice_id': invoice.id})
    #                     if expenses_id.attachment_ids:
    #                         for attachment_id in expenses_id.attachment_ids:
    #                             self.env['ir.attachment'].sudo().create(
    #                                 {
    #                                     'name': attachment_id.name,
    #                                     'type': attachment_id.type,
    #                                     'datas': attachment_id.datas,
    #                                     'mimetype': attachment_id.mimetype,
    #                                     'res_model': invoice._name,
    #                                     'res_id': invoice.id,
    #                                     'res_name': invoice.name,
    #                                 }
    #                             )
    #
    #             get_url = str(self.env['ir.config_parameter'].sudo().search(
    #                 [('key', '=', 'web.base.url')]).value) + '/web?#id=' + str(
    #                 invoice.id) + '&view_type=form&model=account.move&action=' + str(
    #                 action.id) + ' & menu_id = '
    #             prepared_url = '<a href="' + get_url + '" class="btn btn-primary">' + 'View Invoice' + '</a>'
    #             template = self.env.ref(
    #                 'qshield_crm.email_template_of_create_retainer_invoice',
    #                 raise_if_not_found=False)
    #             approver_setting_id = self.env['sale.order.approver.settings'].sudo().search(
    #                 [('finance_user_ids', '!=', False)], limit=1)
    #             partner_to = [str(user.partner_id.id) for user in finance_user_ids if finance_user_ids]
    #             if partner_to:
    #                 template.sudo().with_context(
    #                     partner_to=','.join(partner_to), email_from=self.env.user.email,
    #                     link=prepared_url).send_mail(
    #                     invoice.id, force_send=True)
    #             for finance_user_id in approver_setting_id.finance_user_ids:
    #                 invoice.activity_schedule(
    #                     'qshield_crm.mail_activity_generated_invoice',
    #                     user_id=finance_user_id.id)
