# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_id = fields.Many2one('sale.order',string="Sale order Reference")
    payment_term_id = fields.Many2one('invoice.term.line')