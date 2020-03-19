# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class DocumentsCustom(models.Model):
    _inherit = 'documents.document'

    desc = fields.Text(
        string="Description",
        required=False)
    issue_date = fields.Date(
        string='Issued Date',
        required=False)
    expiry_date = fields.Date(
        required=False)
