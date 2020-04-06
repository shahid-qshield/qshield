# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class DocumentsCustom(models.Model):
    _inherit = 'documents.document'
    _order = 'issue_date desc'

    # _sql_constraints = [
    #     ('document_number_document_type_unique', 'unique (document_number,document_type_id)',
    #      'Document Number and Document Type Combination must be unique !'),
    # ]

    desc = fields.Text(
        string="Description",
        required=False)
    issue_date = fields.Date(
        string='Issued Date',
        required=False)
    expiry_date = fields.Date(
        required=False)

    document_number = fields.Char(
        string='Document Number',
        required=False)
    document_type_id = fields.Many2one(
        comodel_name='ebs_mod.document.types',
        string='Document Type',
        required=False)

    status = fields.Selection(
        string='Status',
        selection=[('na', 'N/A'),
                   ('active', 'Active'), ('expired', 'Expired')],
        default='na',
        required=False, )

    @api.constrains('document_number')
    def _check_document_number(self):
        for rec in self:
            if len(self.env['documents.document'].search(
                    [('document_number', '=', rec.document_number), ('active', '=', True), ('id', '!=', rec.id)])) != 0:
                raise ValidationError(_("Document Number and Document Type Combination must be unique !"))

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         if rec.type:
    #             if rec.type == 'binary':
    #                 if rec.document_number:
    #                     result.append((rec.id, rec.document_number))
    #                 else:
    #                     result.append((rec.id, rec.name))
    #             else:
    #                 result.append((rec.id, rec.name))
    #         else:
    #             result.append((rec.id, rec.name))
    #     return result

    def name_get(self):
        result = []
        for rec in self:
            rec_name = ""
            if rec.document_number:
                rec_name += (rec.document_number + " - ")
            rec_name += rec.name
            result.append((rec.id, rec_name))
        return result

    def write(self, vals):
        # if vals.get('expiry_date', False):
        #     expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d").today().date()
        #     if expiry_date > datetime.today().date():
        #         vals['status'] = 'active'
        #     else:
        #         vals['status'] = 'expired'
        res = super(DocumentsCustom, self).write(vals)
        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise ValidationError(_("Expiry date is before issue date."))
        return res

    def check_document_expiry_date(self):
        for doc in self.env['documents.document'].search([('status', '=', 'active')]):
            if doc.expiry_date:
                if doc.expiry_date < datetime.today().date():
                    doc.status = 'expired'

    @api.model
    def create(self, vals):
        if vals.get('expiry_date', False):
            expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d").date()
            if expiry_date > datetime.today().date():
                vals['status'] = 'active'
            else:
                vals['status'] = 'expired'
        else:
            vals['status'] = 'na'
        res = super(DocumentsCustom, self).create(vals)
        if res.expiry_date and res.issue_date:
            if res.expiry_date < res.issue_date:
                raise ValidationError(_("Expiry date is before issue date."))
        return res

    def preview_document(self):
        self.ensure_one()
        action = {
            'type': "ir.actions.act_url",
            'target': "_blank",
            'url': '/documents/content/preview/%s' % self.id
        }
        return action

    def access_content(self):
        return super(DocumentsCustom, self).access_content()


class DocumentsFolderCustom(models.Model):
    _inherit = 'documents.folder'
    is_default_folder = fields.Boolean(
        string='Is Default Folder',
        required=False
    )
