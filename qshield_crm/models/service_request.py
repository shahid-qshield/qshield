# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api, _


class ServiceRequest(models.Model):
    _inherit = 'ebs_mod.service.request'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string="Sale Order", copy=False)

    def generate_sale_order(self):
        if self.is_out_of_scope or self.is_one_time_transaction:
            order_id = self.env['sale.order'].sudo().create({
                'partner_id': self.partner_id.id,
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


class EbsModContracts(models.Model):
    _inherit = 'ebs_mod.contracts'

    sale_order_id = fields.Many2one(comodel_name='sale.order', string="Sale Order")
    no_of_employees = fields.Integer(string="No Of Employees")


class ExpenseTypes(models.Model):
    _inherit = 'ebs_mod.expense.types'

    product_id = fields.Many2one('product.product', string="Product")


class EbsModServiceRequestExpenses(models.Model):
    _inherit = 'ebs_mod.service.request.expenses'

    attachment_ids = fields.Many2many('ir.attachment', string='Attachment')
    invoice_id = fields.Many2one('account.move', string="Related Invoice")
    to_invoice = fields.Boolean(string="To Invoice", compute="compute_to_invoice")

    def compute_to_invoice(self):
        for rec in self:
            if not rec.invoice_id:
                rec.to_invoice = True
            else:
                rec.to_invoice = False
