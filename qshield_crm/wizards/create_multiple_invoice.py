# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time


class CreateMultipleInvoice(models.TransientModel):
    _name = 'create.multiple.invoice'
    _description = "Create multiple invoices"

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        return self.env['product.product'].browse(int(product_id)).exists()

    invoice_term_ids = fields.Many2many('invoice.term.line')
    product_id = fields.Many2one('product.product', string='Down Payment Product', domain=[('type', '=', 'service')],
                                 default=_default_product_id)

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.product_id.property_account_income_id.id,
            'taxes_id': [(6, 0, self.product_id.taxes_id.ids)],
            'company_id': False,
        }

    def create_invoices(self):
        if self.invoice_term_ids:
            for invoice_term in self.invoice_term_ids:
                order = invoice_term.sale_id
                if invoice_term.type == 'down':
                    if not self.product_id:
                        vals = self._prepare_deposit_product()
                        self.product_id = self.env['product.product'].create(vals)
                        self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id',
                                                                         self.product_id.id)
                    amount, name = self._get_advance_details(invoice_term, order)
                    if self.product_id.invoice_policy != 'order':
                        raise UserError(
                            _('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                    if self.product_id.type != 'service':
                        raise UserError(
                            _("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                    taxes = self.product_id.taxes_id.filtered(
                        lambda r: not order.company_id or r.company_id == order.company_id)
                    if order.fiscal_position_id and taxes:
                        tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id,
                                                                   order.partner_shipping_id).ids
                    else:
                        tax_ids = taxes.ids
                    analytic_tag_ids = []
                    for line in order.order_line:
                        analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                    so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
                    so_line = self.env['sale.order.line'].create(so_line_values)
                    invoice = self._create_invoice(order, so_line, amount, invoice_term, name)
                    if invoice:
                        invoice_term.sudo().write({'invoice_id': invoice})
                elif invoice_term.type == 'regular_invoice':
                    invoice = order._create_invoices(final=False)
                    if invoice:
                        invoice_term.sudo().write({'invoice_id': invoice})
                        invoice.write({'sale_id': invoice_term.sale_id, 'payment_term_id': invoice_term.id})
                elif invoice_term.type == 'regular_invoice_with_deduct':
                    invoice = order._create_invoices(final=True)
                    if invoice:
                        invoice_term.sudo().write({'invoice_id': invoice})
                        invoice.write({'sale_id': invoice_term.sale_id, 'payment_term_id': invoice_term.id})

        else:
            raise UserError('Please Select invoice terms')

    def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
        context = {'lang': order.partner_id.lang}
        so_values = {
            'name': _('Down Payment: %s') % (time.strftime('%m %Y'),),
            'price_unit': amount,
            'product_uom_qty': 0.0,
            'order_id': order.id,
            'discount': 0.0,
            'product_uom': self.product_id.uom_id.id,
            'product_id': self.product_id.id,
            'analytic_tag_ids': analytic_tag_ids,
            'tax_id': [(6, 0, tax_ids)],
            'is_downpayment': True,
        }
        del context
        return so_values

    def _create_invoice(self, order, so_line, amount, invoice_term, name):
        if amount <= 0.0:
            raise UserError('Amount should be positive or grether than zero')
        invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)
        if order.fiscal_position_id:
            invoice_vals['fiscal_position_id'] = order.fiscal_position_id.id
        if invoice_term:
            invoice_vals['sale_id'] = invoice_term.sale_id
            invoice_vals['payment_term_id'] = invoice_term.id
        invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
        invoice.message_post_with_view('mail.message_origin_link',
                                       values={'self': invoice, 'origin': order},
                                       subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    def _get_advance_details(self, invoice_term, order):
        if invoice_term.percentage > 0:
            if all(self.product_id.taxes_id.mapped('price_include')):
                amount = order.amount_total * invoice_term.percentage / 100
            else:
                amount = order.amount_untaxed * invoice_term.percentage / 100
            name = _("Down payment of %s%%") % (invoice_term.percentage)
        elif invoice_term.amount > 0:
            amount = invoice_term.amount
            name = _("Down payment")
        return amount, name

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = {
            'ref': order.client_order_ref,
            'type': 'out_invoice',
            'invoice_origin': order.name,
            'invoice_user_id': order.user_id.id,
            'narration': order.note,
            'partner_id': order.partner_invoice_id.id,
            'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            'partner_shipping_id': order.partner_shipping_id.id,
            'currency_id': order.pricelist_id.currency_id.id,
            'invoice_payment_ref': order.reference,
            'invoice_payment_term_id': order.payment_term_id.id,
            'invoice_partner_bank_id': order.company_id.partner_id.bank_ids[:1].id,
            'team_id': order.team_id.id,
            'campaign_id': order.campaign_id.id,
            'medium_id': order.medium_id.id,
            'source_id': order.source_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'price_unit': amount,
                'quantity': 1.0,
                'product_id': self.product_id.id,
                'product_uom_id': so_line.product_uom.id,
                'tax_ids': [(6, 0, so_line.tax_id.ids)],
                'sale_line_ids': [(6, 0, [so_line.id])],
                'analytic_tag_ids': [(6, 0, so_line.analytic_tag_ids.ids)],
                'analytic_account_id': order.analytic_account_id.id or False,
            })],
        }
        return invoice_vals
