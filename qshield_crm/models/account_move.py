# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    service_request_id = fields.Many2one('ebs_mod.service.request', string="Service Request")
    service_status = fields.Selection(related="service_request_id.status", string="Status")
    related_company_id = fields.Many2one('res.partner', related="service_request_id.related_company_ro",
                                         string="Related Company")
    service_type_id = fields.Many2one('ebs_mod.service.types', string="Service Request Type",
                                      related="service_request_id.service_type_id")
    case_id = fields.Char(related="service_request_id.name")

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
                    values.get('value').update({'attachment_ids': [(6, 0, old_attachment + new_attachment_ids)]})
        return values
