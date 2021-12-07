# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderApprover(models.Model):
    _name = 'sale.order.approver'

    user_id = fields.Many2one("res.users")
    status = fields.Selection([('draft', 'Draft'),
                               ('pending', 'To Approve'),
                               ('approved', 'Approved'),
                               ('refused', 'Refused'),
                               ('cancel', 'Cancel')], string="Status", default="draft")
    sale_order_id = fields.Many2one('sale.order', string="Request", ondelete='cascade')
    approval_date = fields.Datetime(
        string='Approval Date',
        required=False, readonly=True)

    def _create_activity(self):
        for approver in self:
            approver.sale_order_id.activity_schedule(
                'qshield_crm.mail_activity_data_sale_order',
                user_id=approver.user_id.id)

