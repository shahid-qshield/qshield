# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderApproverSettings(models.Model):
    _name = 'sale.order.approver.settings'

    name = fields.Char(string="Name")
    approver_ids = fields.Many2many('res.users')