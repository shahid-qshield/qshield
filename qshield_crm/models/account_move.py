# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round as round, float_compare
import base64
import xlsxwriter
import io
from itertools import groupby


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order', string="Sale order Reference")
    payment_term_id = fields.Many2one('invoice.term.line')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('new', 'New'),
        ('approve', 'Approve'),
        ('posted', 'Lock'),
        ('cancel', 'Cancelled')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    qshield_invoice_type = fields.Selection(
        [('retainer', 'Retainer'), ('out_of_scope_retainer', 'Out of Scope Retainer'),
         ('out_of_scope_one_time_payment', 'Out of Scope One time Payment'),
         ('one_time_payment', 'One Time Payment'), ('expense_invoice', 'Expense Invoice')])
    partner_invoice_type = fields.Selection(related="partner_id.partner_invoice_type")

    retainer_amount = fields.Float('Retainer Amount', compute='get_retainer_amount')
    binary_data = fields.Binary("File")

    @api.depends('invoice_line_ids')
    def get_retainer_amount(self):
        for rec in self:
            amount = 0.0
            if rec.invoice_line_ids:
                amount = sum(rec.invoice_line_ids.filtered(
                    lambda x: x.service_request_id.is_in_scope and not x.is_government_fees_line).mapped(
                    'price_subtotal'))
            rec.retainer_amount = amount

    @api.model
    def print_excel_invoice_report(self):
        filename = self._get_expense_report_file_name() +'.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center'})
        format1 = workbook.add_format({'font_size': 10, 'align': 'center'})
        sheet = workbook.add_worksheet('Invoices')
        sheet.set_column(0, 2, 30)
        sheet.set_column(4, 5, 30)
        sheet.set_column(3, 3, 20)
        sheet.set_column(7, 11, 25)
        sheet.write(0, 0, 'Company', header_format)
        sheet.write(0, 1, 'Invoice Number', header_format)
        sheet.write(0, 2, 'Product', header_format)
        sheet.write(0, 3, 'Description', header_format)
        sheet.write(0, 4, 'Service Request', header_format)
        sheet.write(0, 5, 'Service Request Contact', header_format)
        sheet.write(0, 6, 'Service Request Type', header_format)
        sheet.write(0, 7, 'Status', header_format)
        sheet.write(0, 8, 'Label', header_format)
        sheet.write(0, 9, 'Government Fees', header_format)
        sheet.write(0, 10, 'Service Fees', header_format)
        row = 1
        sheet.write(row, 0, self.partner_id.name, format1)
        sheet.write(row, 1, self.name, format1)
        if self.invoice_line_ids:
            in_scope_service = self.invoice_line_ids.mapped('service_request_id').filtered(
                lambda s: s.is_in_scope)
            in_scope_invoice_line_ids = self.env['account.move.line']
            total_retainer_amount = 0.0
            for contract, contract_in_scope_services in groupby(in_scope_service, key=lambda s: s.contract_id):
                amount = 0.0
                service_requests = list(contract_in_scope_services)
                move_lines = self.invoice_line_ids.filtered(
                    lambda s: s.service_request_id in service_requests and not s.is_government_fees_line)
                in_scope_invoice_line_ids += move_lines
                amount += sum(move_lines.mapped('price_subtotal'))
                total_retainer_amount += amount
                sheet.write(row, 2, 'Retainer' + contract.name, format1)
                sheet.write(row, 3, 'Retainer' + contract.name, format1)
                sheet.write(row, 4, '', format1)
                sheet.write(row, 5, contract.contact_id.name if contract.contact_id else '', format1)
                sheet.write(row, 6, '', format1)
                sheet.write(row, 7, '', format1)
                sheet.write(row, 8, '', format1)
                sheet.write(row, 9, 0.0, format1)
                sheet.write(row, 10, round(amount, precision_digits=2), format1)
                row += 1
                for move_line in move_lines:
                    sheet.write(row, 2, move_line.product_id.name, format1)
                    sheet.write(row, 3, move_line.description, format1)
                    sheet.write(row, 4, move_line.service_request_id.name if move_line.service_request_id else '',
                                format1)
                    sheet.write(row, 5, move_line.service_partner_id.name if move_line.service_request_id else '',
                                format1)
                    sheet.write(row, 6, move_line.service_type_id.name if move_line.service_request_id else '',
                                format1)
                    sheet.write(row, 7, move_line.service_status if move_line.service_request_id else '', format1)
                    sheet.write(row, 8, move_line.name if move_line.name else '', format1)
                    sheet.write(row, 9, '', format1)
                    sheet.write(row, 10, '', format1)
                    row += 1
            total_government_fees = 0.0
            total_out_scope_amount = 0.0
            for line in self.invoice_line_ids.filtered(lambda s: s not in in_scope_invoice_line_ids):
                sheet.write(row, 2, line.product_id.name, format1)
                sheet.write(row, 3, line.description, format1)
                sheet.write(row, 4, line.service_request_id.name if line.service_request_id else '', format1)
                sheet.write(row, 5, line.service_partner_id.name if line.service_request_id else '', format1)
                sheet.write(row, 6, line.service_type_id.name if line.service_request_id else '', format1)
                sheet.write(row, 7, line.service_status if line.service_request_id else '', format1)
                sheet.write(row, 8, line.name if line.name else '', format1)
                if line.is_government_fees_line:
                    total_government_fees += line.price_subtotal
                    sheet.write(row, 9, round(line.price_subtotal,precision_digits=2), format1)
                else:
                    sheet.write(row, 9, 0.0, format1)
                if not line.is_government_fees_line:
                    sheet.write(row, 10, round(line.price_subtotal,precision_digits=2), format1)
                    total_out_scope_amount += line.price_subtotal
                else:
                    sheet.write(row, 10, 0.0, format1)
                row += 1
            row += 1
            style_highlight = workbook.add_format(
                {'bold': True, 'pattern': 1, 'bg_color': '#E0E0E0', 'align': 'center'})
            merge_string = 'A' + str(row) + ':K' + str(row)
            retainer_string = 'Total Retainer Amount:- ' + str(round(total_retainer_amount,precision_digits=2))
            sheet.merge_range(merge_string, retainer_string, style_highlight)
            row += 1
            merge_string = 'A' + str(row) + ':K' + str(row)
            government_string = 'Total Government Fees :- ' + str(round(total_government_fees,precision_digits=2))
            sheet.merge_range(merge_string, government_string, style_highlight)
            row += 1
            merge_string = 'A' + str(row) + ':K' + str(row)
            out_of_scope_string = 'Total Out of scope :- ' + str(round(total_out_scope_amount,precision_digits=2))
            sheet.merge_range(merge_string, out_of_scope_string, style_highlight)
            row += 1
            row += 1
            merge_string = 'A' + str(row) + ':K' + str(row)
            total_string = 'Total :- ' + str(round((total_out_scope_amount+total_retainer_amount+total_government_fees),precision_digits=2))
            sheet.merge_range(merge_string, total_string, style_highlight)
            row += 1
        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        temporary_record = self[0]
        temporary_record.write({'binary_data': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=account.move&field=binary_data&download=true&id=%s&filename=%s' % (
                temporary_record.id, filename),
            'target': 'new',
        }

    def _get_expense_report_file_name(self):
        name = self.partner_id.name
        if self.invoice_date:
            name += "_" + self.invoice_date.strftime('%m/%d/%Y')
        return name

    def action_invoice_submit(self):
        self.sudo().write({'state': 'new'})

    def action_invoice_approve(self):
        self.sudo().write({'state': 'approve'})

    def confirm_invoice(self):
        for record in self:
            record.action_invoice_submit()

    def approve_invoice(self):
        for record in self:
            record.action_invoice_approve()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    description = fields.Char(string="Description")

    service_request_id = fields.Many2one('ebs_mod.service.request', string="Service Request")
    service_status = fields.Selection(related="service_request_id.status", string="Status")
    related_company_id = fields.Many2one('res.partner', related="service_request_id.related_company_ro",
                                         string="Related Company")
    service_type_id = fields.Many2one('ebs_mod.service.types', string="Service Request Type",
                                      related="service_request_id.service_type_id")
    case_id = fields.Char(related="service_request_id.name")
    is_government_fees_line = fields.Boolean(string="Is Goverment Fees Line")
    price_unit = fields.Float(string='Unit Price', digits=(12, 8))
    price_subtotal = fields.Float(string='Subtotal', store=True, readonly=True, digits=(12, 8))
    service_partner_id = fields.Many2one(string="Service Contact", related="service_request_id.partner_id")

    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes,
                                            move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        subtotal = quantity * price_unit_wo_discount

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.with_context(force_sign=1, custom_context=True).compute_all(
                price_unit_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner,
                is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        # In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        values = super(MailComposer, self).onchange_template_id(template_id, composition_mode, model, res_id)
        if self._context.get('default_res_model') == 'account.move' and self._context.get('active_ids'):
            invoice_ids = self.env['account.move'].sudo().browse(self._context.get('active_ids'))
            for invoice_id in invoice_ids:
                attachment_ids = self.env['ir.attachment'].sudo().search(
                    [('res_model', '=', 'account.move'), ('res_id', '=', invoice_id.id)])
                new_attachment_ids = []
                for attachment_id in attachment_ids:
                    data_attach = {
                        'name': attachment_id.name,
                        'datas': attachment_id.datas,
                        'res_model': 'mail.compose.message',
                        'res_id': 0,
                        'type': 'binary',  # override default_type from context, possibly meant for another model!
                    }
                    new_attachment_ids.append(self.env['ir.attachment'].sudo().create(data_attach).id)
                if values.get('value') and values.get('value').get('attachment_ids'):
                    old_attachment = values.get('value').get('attachment_ids')[0][2]
                    values.get('value').update({'attachment_ids': [(6, 0, new_attachment_ids)]})
        return values


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False,
                    handle_price_include=True):
        """ Returns all information required to apply taxes (in self + their children in case of a tax group).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

            'handle_price_include' is used when we need to ignore all tax included in price. If False, it means the
            amount passed to this method will be considered as the base of all computations.

        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'total_void'    : 0.0,    # Total with those taxes, that don't have an account set
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }],
        } """
        if not self:
            company = self.env.company
        else:
            company = self[0].company_id

        # 1) Flatten the taxes.
        taxes, groups_map = self.flatten_taxes_hierarchy(create_map=True)

        # 2) Avoid mixing taxes having price_include=False && include_base_amount=True
        # with taxes having price_include=True. This use case is not supported as the
        # computation of the total_excluded would be impossible.
        base_excluded_flag = False  # price_include=False && include_base_amount=True
        included_flag = False  # price_include=True
        for tax in taxes:
            if tax.price_include:
                included_flag = True
            elif tax.include_base_amount:
                base_excluded_flag = True
            if base_excluded_flag and included_flag:
                raise UserError(
                    _('Unable to mix any taxes being price included with taxes affecting the base amount but not included in price.'))

        # 3) Deal with the rounding methods
        if not currency:
            currency = company.currency_id

        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        prec = currency.rounding

        # In some cases, it is necessary to force/prevent the rounding of the tax and the total
        # amounts. For example, in SO/PO line, we don't want to round the price unit at the
        # precision of the currency.
        # The context key 'round' allows to force the standard behavior.
        round_tax = False if company.tax_calculation_rounding_method == 'round_globally' else True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])

        if not round_tax:
            prec *= 1e-5

        # 4) Iterate the taxes in the reversed sequence order to retrieve the initial base of the computation.
        #     tax  |  base  |  amount  |
        # /\ ----------------------------
        # || tax_1 |  XXXX  |          | <- we are looking for that, it's the total_excluded
        # || tax_2 |   ..   |          |
        # || tax_3 |   ..   |          |
        # ||  ...  |   ..   |    ..    |
        #    ----------------------------
        def recompute_base(base_amount, fixed_amount, percent_amount, division_amount):
            # Recompute the new base amount based on included fixed/percent amounts and the current base amount.
            # Example:
            #  tax  |  amount  |   type   |  price_include  |
            # -----------------------------------------------
            # tax_1 |   10%    | percent  |  t
            # tax_2 |   15     |   fix    |  t
            # tax_3 |   20%    | percent  |  t
            # tax_4 |   10%    | division |  t
            # -----------------------------------------------

            # if base_amount = 145, the new base is computed as:
            # (145 - 15) / (1.0 + 30%) * 90% = 130 / 1.3 * 90% = 90
            return (base_amount - fixed_amount) / (1.0 + percent_amount / 100.0) * (100 - division_amount) / 100

        # The first/last base must absolutely be rounded to work in round globally.
        # Indeed, the sum of all taxes ('taxes' key in the result dictionary) must be strictly equals to
        # 'price_included' - 'price_excluded' whatever the rounding method.
        #
        # Example using the global rounding without any decimals:
        # Suppose two invoice lines: 27000 and 10920, both having a 19% price included tax.
        #
        #                   Line 1                      Line 2
        # -----------------------------------------------------------------------
        # total_included:   27000                       10920
        # tax:              27000 / 1.19 = 4310.924     10920 / 1.19 = 1743.529
        # total_excluded:   22689.076                   9176.471
        #
        # If the rounding of the total_excluded isn't made at the end, it could lead to some rounding issues
        # when summing the tax amounts, e.g. on invoices.
        # In that case:
        #  - amount_untaxed will be 22689 + 9176 = 31865
        #  - amount_tax will be 4310.924 + 1743.529 = 6054.453 ~ 6054
        #  - amount_total will be 31865 + 6054 = 37919 != 37920 = 27000 + 10920
        #
        # By performing a rounding at the end to compute the price_excluded amount, the amount_tax will be strictly
        # equals to 'price_included' - 'price_excluded' after rounding and then:
        #   Line 1: sum(taxes) = 27000 - 22689 = 4311
        #   Line 2: sum(taxes) = 10920 - 2176 = 8744
        #   amount_tax = 4311 + 8744 = 13055
        #   amount_total = 31865 + 13055 = 37920

        if self._context.get('custom_context'):
            base = (price_unit * quantity)
        else:
            base = currency.round(price_unit * quantity)

        # For the computation of move lines, we could have a negative base value.
        # In this case, compute all with positive values and negate them at the end.
        sign = 1
        if currency.is_zero(base):
            sign = self._context.get('force_sign', 1)
        elif base < 0:
            sign = -1
        if base < 0:
            base = -base

        # Store the totals to reach when using price_include taxes (only the last price included in row)
        total_included_checkpoints = {}
        i = len(taxes) - 1
        store_included_tax_total = True
        # Keep track of the accumulated included fixed/percent amount.
        incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
        # Store the tax amounts we compute while searching for the total_excluded
        cached_tax_amounts = {}
        if handle_price_include:
            for tax in reversed(taxes):
                tax_repartition_lines = (
                        is_refund
                        and tax.refund_repartition_line_ids
                        or tax.invoice_repartition_line_ids
                ).filtered(lambda x: x.repartition_type == "tax")
                sum_repartition_factor = sum(tax_repartition_lines.mapped("factor"))

                if tax.include_base_amount:
                    base = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)
                    incl_fixed_amount = incl_percent_amount = incl_division_amount = 0
                    store_included_tax_total = True
                if tax.price_include or self._context.get('force_price_include'):
                    if tax.amount_type == 'percent':
                        incl_percent_amount += tax.amount * sum_repartition_factor
                    elif tax.amount_type == 'division':
                        incl_division_amount += tax.amount * sum_repartition_factor
                    elif tax.amount_type == 'fixed':
                        incl_fixed_amount += quantity * tax.amount * sum_repartition_factor
                    else:
                        # tax.amount_type == other (python)
                        tax_amount = tax._compute_amount(base, sign * price_unit, abs(quantity), product,
                                                         partner) * sum_repartition_factor
                        incl_fixed_amount += tax_amount
                        # Avoid unecessary re-computation
                        cached_tax_amounts[i] = tax_amount
                    # In case of a zero tax, do not store the base amount since the tax amount will
                    # be zero anyway. Group and Python taxes have an amount of zero, so do not take
                    # them into account.
                    if store_included_tax_total and (
                            tax.amount or tax.amount_type not in ("percent", "division", "fixed")
                    ):
                        total_included_checkpoints[i] = base
                        store_included_tax_total = False
                i -= 1

        if self._context.get('custom_context'):
            total_excluded = recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount)
        else:
            total_excluded = currency.round(
                recompute_base(base, incl_fixed_amount, incl_percent_amount, incl_division_amount))

        # 5) Iterate the taxes in the sequence order to compute missing tax amounts.
        # Start the computation of accumulated amounts at the total_excluded value.
        base = total_included = total_void = total_excluded

        taxes_vals = []
        i = 0
        cumulated_tax_included_amount = 0
        for tax in taxes:
            tax_repartition_lines = (
                    is_refund and tax.refund_repartition_line_ids or tax.invoice_repartition_line_ids).filtered(
                lambda x: x.repartition_type == 'tax')
            sum_repartition_factor = sum(tax_repartition_lines.mapped('factor'))

            price_include = self._context.get('force_price_include', tax.price_include)

            # compute the tax_amount
            if price_include and total_included_checkpoints.get(i) is not None and sum_repartition_factor != 0:
                # We know the total to reach for that tax, so we make a substraction to avoid any rounding issues
                tax_amount = total_included_checkpoints[i] - (base + cumulated_tax_included_amount)
                cumulated_tax_included_amount = 0
            else:
                tax_amount = tax.with_context(force_price_include=False)._compute_amount(
                    base, sign * price_unit, quantity, product, partner)

            # Round the tax_amount multiplied by the computed repartition lines factor.
            tax_amount = round(tax_amount, precision_rounding=prec)
            factorized_tax_amount = round(tax_amount * sum_repartition_factor, precision_rounding=prec)

            if price_include and total_included_checkpoints.get(i) is None:
                cumulated_tax_included_amount += factorized_tax_amount

            # If the tax affects the base of subsequent taxes, its tax move lines must
            # receive the base tags and tag_ids of these taxes, so that the tax report computes
            # the right total
            subsequent_taxes = self.env['account.tax']
            subsequent_tags = self.env['account.account.tag']
            if tax.include_base_amount:
                subsequent_taxes = taxes[i + 1:]
                subsequent_tags = subsequent_taxes.get_tax_tags(is_refund, 'base')

            # Compute the tax line amounts by multiplying each factor with the tax amount.
            # Then, spread the tax rounding to ensure the consistency of each line independently with the factorized
            # amount. E.g:
            #
            # Suppose a tax having 4 x 50% repartition line applied on a tax amount of 0.03 with 2 decimal places.
            # The factorized_tax_amount will be 0.06 (200% x 0.03). However, each line taken independently will compute
            # 50% * 0.03 = 0.01 with rounding. It means there is 0.06 - 0.04 = 0.02 as total_rounding_error to dispatch
            # in lines as 2 x 0.01.
            repartition_line_amounts = [round(tax_amount * line.factor, precision_rounding=prec) for line in
                                        tax_repartition_lines]
            total_rounding_error = round(factorized_tax_amount - sum(repartition_line_amounts), precision_rounding=prec)
            nber_rounding_steps = int(abs(total_rounding_error / currency.rounding))
            rounding_error = round(nber_rounding_steps and total_rounding_error / nber_rounding_steps or 0.0,
                                   precision_rounding=prec)

            for repartition_line, line_amount in zip(tax_repartition_lines, repartition_line_amounts):

                if nber_rounding_steps:
                    line_amount += rounding_error
                    nber_rounding_steps -= 1

                taxes_vals.append({
                    'id': tax.id,
                    'name': partner and tax.with_context(lang=partner.lang).name or tax.name,
                    'amount': sign * line_amount,
                    'base': round(sign * base, precision_rounding=prec),
                    'sequence': tax.sequence,
                    'account_id': tax.cash_basis_transition_account_id.id if tax.tax_exigibility == 'on_payment' else repartition_line.account_id.id,
                    'analytic': tax.analytic,
                    'price_include': price_include,
                    'tax_exigibility': tax.tax_exigibility,
                    'tax_repartition_line_id': repartition_line.id,
                    'group': groups_map.get(tax),
                    'tag_ids': (repartition_line.tag_ids + subsequent_tags).ids,
                    'tax_ids': subsequent_taxes.ids,
                })

                if not repartition_line.account_id:
                    total_void += line_amount

            # Affect subsequent taxes
            if tax.include_base_amount:
                base += factorized_tax_amount

            total_included += factorized_tax_amount
            i += 1

        if self._context.get('custom_context'):
            return {
                'base_tags': taxes.mapped(
                    is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids').filtered(
                    lambda x: x.repartition_type == 'base').mapped('tag_ids').ids,
                'taxes': taxes_vals,
                'total_excluded': sign * total_excluded,
                'total_included': sign * total_included,
                'total_void': sign * total_void,
            }
        else:
            return {
                'base_tags': taxes.mapped(
                    is_refund and 'refund_repartition_line_ids' or 'invoice_repartition_line_ids').filtered(
                    lambda x: x.repartition_type == 'base').mapped('tag_ids').ids,
                'taxes': taxes_vals,
                'total_excluded': sign * total_excluded,
                'total_included': sign * currency.round(total_included),
                'total_void': sign * currency.round(total_void),
            }
