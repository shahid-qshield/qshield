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
        string='Notify For Expiry',
        required=False,
        default=False)
    days_before_notifaction = fields.Integer(
        string='Days Before Expiry'
    )
    expiry_configuration_ids = fields.Many2many('document.types.expiry.configuration',
                                                string="Days Before Expiry Configuration")
    type = fields.Selection(string="Type", selection=[('passport', 'Passport'), ('qatar_id', 'Qatar ID')])


class DocumentTypesExpiryConfiguration(models.Model):
    _name = 'document.types.expiry.configuration'
    _description = "Document Type Expiry Configuration"
    _rec_name = 'days_before_notification'

    days_before_notification = fields.Integer(
        string='Days Before Expiry'
    )
