# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


class DocumentsCustom(models.Model):
    _inherit = 'documents.document'
    _order = 'issue_date desc'

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

    def name_get(self):
        result = []
        for rec in self:
            if rec.type:
                if rec.type == 'binary':
                    if rec.document_number:
                        result.append((rec.id, rec.document_number))
                    else:
                        result.append((rec.id, rec.name))
                else:
                    result.append((rec.id, rec.name))
            else:
                result.append((rec.id, rec.name))
        return result

    def write(self, vals):
        res = super(DocumentsCustom, self).write(vals)
        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise ValidationError(_("Expiry date is before issue date."))
        return res

    @api.model
    def create(self, vals):
        if 'expiry_date' in vals and vals['expiry_date']:
            expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d")
            if expiry_date > datetime.today().date():
                vals['status'] = 'active'
            else:
                vals['status'] = 'expired'
        else:
            vals['status'] = 'na'
        res = super(DocumentsCustom, self).create(vals)
        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise ValidationError(_("Expiry date is before issue date."))


class DocumentsFolderCustom(models.Model):
    _inherit = 'documents.folder'
    is_default_folder = fields.Boolean(
        string='Is Default Folder',
        required=False
    )
