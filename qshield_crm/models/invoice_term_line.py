# -*- coding: utf-8 -*-

from odoo import models, fields, api


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

    def compute_to_invoice(self):
        for rec in self:
            if not rec.invoice_id:
                rec.to_invoice = True
            else:
                rec.to_invoice = False
