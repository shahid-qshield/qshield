# -*- coding: utf-8 -*-
from docutils.nodes import document

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CreateContactDocument(models.TransientModel):
    _name = 'ebs_mod.contact.document'
    _description = 'Create documents for contacts wizard'

    document_number = fields.Char(
        string='Document Number',
        required=True)

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

    service_request_id = fields.Many2one(
        comodel_name='ebs_mod.service.request',
        string='Service',
        required=False)
    attachment_ids = fields.Many2many(comodel_name="ir.attachment",
                                      relation="ebs_mod_m2m_ir_contact_document",
                                      column1="m2m_id",
                                      column2="attachment_id",
                                      string="File"
                                      )

    binary = fields.Binary(string='Icon')

    desc = fields.Text(
        string="Description",
        required=False)

    document_type_id = fields.Many2one(
        comodel_name='ebs_mod.document.types',
        string='Document Type',
        required=True)

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
        vals = {
            'document_type_id': self.document_type_id.id,
            'document_number': self.document_number,
            'issue_date': self.issue_date.strftime("%Y-%m-%d"),
            'desc': self.desc,
            'tag_ids': self.tags,
            'attachment_id': self.attachment_ids[0].id,
            'type': 'binary',
            'folder_id': folder.id
        }
        if self.env.context.get('upload_contact', False):
            vals.update({'partner_id': self.contact_id.id})
        if self.env.context.get('upload_service', False):
            vals.update({'service_id': self.service_request_id.id})
            vals.update({'res_id': self.service_request_id.id})
            vals.update({'res_model': self.service_request_id._name})
        if self.env.context.get('upload_service_contact', False):
            vals.update({'service_id': self.service_request_id.id})
            vals.update({'res_id': self.service_request_id.id})
            vals.update({'res_model': self.service_request_id._name})
            vals.update({'partner_id': self.contact_id.id})

        if self.expiry_date:
            vals.update({'expiry_date': self.expiry_date.strftime("%Y-%m-%d")})
        document = self.env['documents.document'].create(vals)
        self.env.cr.commit()
        # 👇 Create activity on the service request to appear in its chatter
        if self.service_request_id:
            activity_vals = {
                'res_model_id': self.env['ir.model']._get('ebs_mod.service.request').id,
                'res_id': self.service_request_id.id,
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': 'Document Uploaded',
                'note': f'Document "{document.name or document.document_number}" has been uploaded.',
                'user_id': self.env.user.id,
                'date_deadline': fields.Date.today(),
            }
            self.env['mail.activity'].create(activity_vals)