# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DocumentTypes(models.Model):
    _name = 'ebs_mod.document.types'
    _description = "Document Type"


    _sql_constraints = [
        ('document_type_name_unique', 'unique (name)',
         'Name must be unique !'),
    ]

    name = fields.Char(
        string='Name',
        required=True)

    notify = fields.Boolean(
        string='Notified For Expiration',
        required=False,
        default=False)
    days_before_notifaction = fields.Integer(
        string='Days Before Expiration'
    )
