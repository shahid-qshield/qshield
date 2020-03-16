# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DocumentType(models.Model):
    _name = 'ebs_mod.document.type'
    _description = "Document Type"

    value = fields.Char(
        string="Search Key",
        required=True)
    name = fields.Char(
        string='Name',
        required=True)