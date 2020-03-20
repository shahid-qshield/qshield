# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CreateContactDocument(models.TransientModel):
    _name = 'ebs_mod.contact.document'
    _description = 'Create documents for contacts wizard'

    issue_date = fields.Date(
        string='Issue Date',
        required=True)
    expiry_date = fields.Date(
        string='Expiry Date',
        required=False)
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=False)
    attachment_ids = fields.Many2many(comodel_name="ir.attachment",
                                       relation="ebs_mod_m2m_ir_contact_document",
                                       column1="m2m_id",
                                       column2="attachment_id",
                                       string="File"
                                       )
    desc = fields.Text(
        string="Description",
        required=False)

    tags = fields.Many2many(
        comodel_name='documents.tag',
        relation="ebs_mod_m2m_ir_contact_document_tags",
        column1="m2m_id",
        column2="tag_id",
        string='Tags')

    def create_document(self):
        folder = self.env['documents.folder'].search([('is_default_folder', '=', True)], limit=1)
        if len(self.attachment_ids) == 0 or len(self.attachment_ids) > 1:
            raise ValidationError(_("Select 1 File"))

        if len(self.tags) == 0:
            raise ValidationError(_("Select Tags"))
        self.env['documents.document'].create(
            {
                'issue_date': self.issue_date,
                'expiry_date': self.expiry_date,
                'desc': self.desc,
                'tag_ids': self.tags,
                'attachment_id': self.attachment_ids[0].id,
                'partner_id': self.contact_id.id,
                'type': 'binary',
                'folder_id': folder.id

            }
        )
        self.env.cr.commit()
