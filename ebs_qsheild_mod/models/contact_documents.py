# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ContactDocument(models.Model):
    _name = 'ebs_mod.contact.document'
    _description = "Contact Document"

    type = fields.Many2one(
        comodel_name='ebs_mod.document.type',
        string='Type',
        required=True)
    attachment = fields.Many2many(comodel_name="ir.attachment",
                                relation="ebs_mod_m2m_ir_contact_document",
                                column1="m2m_id",
                                column2="attachment_id",
                                string="File")
    desc = fields.Text(
        string="Description",
        required=False)
    issue_date = fields.Date(
        string='Issued Date',
        required=False)
    expiry_date = fields.Date(
        required=False)
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=True)

