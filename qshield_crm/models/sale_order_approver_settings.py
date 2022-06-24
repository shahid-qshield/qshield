# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderApproverSettings(models.Model):
    _name = 'sale.order.approver.settings'

    name = fields.Char(string="Name")
    approver_ids = fields.Many2many('res.users')
    type = fields.Selection([('service_approver', 'Service Approver'), ('crm_approver', 'CRM Approver')])
    service_approver_notification_email = fields.Text(string="Service Approver Notification Emails")
    finance_user_ids = fields.Many2many('res.users', 'approver_setting_id', string="Finance Department user")
