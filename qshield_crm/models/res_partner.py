# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        res = super(ResPartner, self).default_get(fields)
        if 'property_account_receivable_id' in fields and 'property_account_payable_id' in fields:
            property_account_receivable_id = self.env['account.account'].search(
                [('internal_type', '=', 'receivable'), ('deprecated', '=', False),
                 ('company_id', '=', self.env.company.id)], limit=1)
            property_account_payable_id = self.env['account.account'].search(
                [('internal_type', '=', 'payable'), ('deprecated', '=', False),
                 ('company_id', '=', self.env.company.id)], limit=1)
            res.update({
                'property_account_receivable_id': property_account_receivable_id and property_account_receivable_id.id or False,
                'property_account_payable_id': property_account_payable_id and property_account_payable_id.id or False})
        return res

    partner_invoice_type = fields.Selection(
        [('retainer', 'Retainer'), ('per_transaction', 'Per Transaction'),
         ('one_time_transaction', 'One time Transaction'),
         ('partners', 'Partners'), ('outsourcing', 'Outsourcing')])

    pending_invoice_count = fields.Integer(compute="compute_pending_invoice_count", string="Pending invoice count")
    expense_invoice_count = fields.Integer(compute="compute_expense_invoice_count", string="Expense invoice count")
    iban_number = fields.Char(string="IBAN Number")
    is_editable_partner_invoice_type = fields.Boolean(compute="compute_is_editable_partner_invoice_type")
    is_editable_pricelist = fields.Boolean(compute="compute_is_editable_partner_invoice_type")
    parent_company_id = fields.Many2one('res.partner',string="Related Parent Company")


    @api.depends()
    def compute_is_editable_partner_invoice_type(self):
        for record in self:
            is_editable_partner_invoice_type = False
            is_editable_pricelist = False
            if self.env.user.has_group('qshield_crm.editable_partner_invoice_type'):
                is_editable_partner_invoice_type = True
            if self.env.user.has_group('base.group_system'):
                is_editable_pricelist = True
            record.is_editable_partner_invoice_type = is_editable_partner_invoice_type
            record.is_editable_pricelist = is_editable_pricelist

    @api.model
    def create(self, values):
        res = super(ResPartner, self).create(values)
        for record in res:
            if self._context.get('partner_invoice_type'):
                record.partner_invoice_type = self._context.get('partner_invoice_type')
                record.person_type = 'company'
            if self._context.get('parent_company_id'):
                record.parent_company_id = self._context.get('parent_company_id')
                record.person_type = 'company'
            if record.person_type in ['emp', 'visitor', 'child'] and record.related_company:
                record.partner_invoice_type = record.related_company.partner_invoice_type
            if record.person_type == 'company' and record.parent_company_id:
                record.partner_invoice_type = record.parent_company_id.partner_invoice_type
        return res

    def write(self, vals):
        if vals.get('person_type') == 'child':
            if vals.get('parent_id'):
                related_company = self.search([('parent_id', '=', vals.get('parent_id'))])
                if related_company:
                    vals.update({'partner_invoice_type': related_company.partner_invoice_type})
            elif self.related_company and self.related_company.partner_invoice_type:
                vals.update({'partner_invoice_type': self.related_company.partner_invoice_type})
        elif vals.get('person_type') in ['emp', 'visitor']:
            if vals.get('parent_id'):
                related_company = self.search([('id', '=', vals.get('parent_id'))])
                if related_company:
                    vals.update({'partner_invoice_type': related_company.partner_invoice_type})
            elif self.related_company and self.related_company.partner_invoice_type:
                vals.update({'partner_invoice_type': self.related_company.partner_invoice_type})
        elif vals.get('person_type') == 'company':
            if vals.get('parent_company_id'):
                parent_company_id = self.search([('id', '=', vals.get('parent_company_id'))])
                if parent_company_id:
                    vals.update({'partner_invoice_type': parent_company_id.partner_invoice_type})
            elif self.parent_company_id and self.parent_company_id.partner_invoice_type:
                vals.update({'partner_invoice_type': self.parent_company_id.partner_invoice_type})
        if vals.get('parent_id') and not vals.get('person_type'):
            related_company = self.search([('id', '=', vals.get('parent_id'))])
            if related_company:
                vals.update({'partner_invoice_type': related_company.partner_invoice_type})
        if vals.get('parent_company_id') and not vals.get('person_type'):
            parent_company_id = self.search([('id', '=', vals.get('parent_company_id'))])
            if parent_company_id:
                vals.update({'partner_invoice_type': parent_company_id.partner_invoice_type})
        res = super(ResPartner, self).write(vals)
        return res

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
            sale_order_ids = self.env['sale.order'].sudo().search(
                [('partner_id', '=', rec.id), ('invoice_term_ids', '!=', False)])
            if sale_order_ids:
                invoice_term_lines = sale_order_ids.sudo().mapped('invoice_term_ids')
                if invoice_term_lines:
                    pending_invoice_count = len(invoice_term_lines)
            rec.pending_invoice_count = pending_invoice_count

    def action_pending_invoice(self):
        sale_order_ids = self.env['sale.order'].sudo().search(
            [('partner_id', '=', self.id), ('invoice_term_ids', '!=', False)])
        invoice_term_line_ids = []
        if sale_order_ids:
            invoice_term_lines = sale_order_ids.sudo().mapped('invoice_term_ids')
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


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    custom_account_type = fields.Selection(
        [('current_account', 'Current Account'), ('saving_account', 'Saving Account')])
