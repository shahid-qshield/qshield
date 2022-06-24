# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_invoice_type = fields.Selection(
        [('retainer', 'Retainer'), ('per_transaction', 'Per Transaction'),
         ('one_time_transaction', 'One time Transaction'),
         ('partners', 'Partners'), ('outsourcing', 'Outsourcing')])

    pending_invoice_count = fields.Integer(compute="compute_pending_invoice_count", string="Pending invoice count")
    expense_invoice_count = fields.Integer(compute="compute_expense_invoice_count", string="Expense invoice count")

    def compute_expense_invoice_count(self):
        for rec in self:
            expense_invoice_count = 0
            service_request_ids = self.env['ebs_mod.service.request'].search(
                [('partner_id', '=', rec.id), ('expenses_ids', '!=', False)])
            if service_request_ids:
                expenses_ids = service_request_ids.mapped('expenses_ids')
                if expenses_ids:
                    expense_invoice_count = len(expenses_ids)
            rec.expense_invoice_count = expense_invoice_count

    def action_expense_invoice(self):
        service_request_ids = self.env['ebs_mod.service.request'].search(
            [('partner_id', '=', self.id), ('expenses_ids', '!=', False)])
        expenses_ids = []
        if service_request_ids:
            expenses_ids = service_request_ids.mapped('expenses_ids').ids
        return {
            'name': _('Expense Invoices'),
            'view_mode': 'tree,form',
            'res_model': 'ebs_mod.service.request.expenses',
            'domain': [('id', 'in', expenses_ids)],
            'type': 'ir.actions.act_window',
            'context': {'search_default_current_month': 1}
        }

    def compute_pending_invoice_count(self):
        for rec in self:
            pending_invoice_count = 0
            sale_order_ids = self.env['sale.order'].search(
                [('partner_id', '=', rec.id), ('invoice_term_ids', '!=', False)])
            if sale_order_ids:
                invoice_term_lines = sale_order_ids.mapped('invoice_term_ids')
                if invoice_term_lines:
                    pending_invoice_count = len(invoice_term_lines)
            rec.pending_invoice_count = pending_invoice_count

    def action_pending_invoice(self):
        sale_order_ids = self.env['sale.order'].search(
            [('partner_id', '=', self.id), ('invoice_term_ids', '!=', False)])
        invoice_term_line_ids = []
        if sale_order_ids:
            invoice_term_lines = sale_order_ids.mapped('invoice_term_ids')
            if invoice_term_lines:
                invoice_term_line_ids = invoice_term_lines.ids
        return {
            'name': _('Service Invoices'),
            'view_mode': 'tree',
            'res_model': 'invoice.term.line',
            'domain': [('id', 'in', invoice_term_line_ids)],
            'type': 'ir.actions.act_window',
            'context': {'search_default_current_month': 1}
        }
