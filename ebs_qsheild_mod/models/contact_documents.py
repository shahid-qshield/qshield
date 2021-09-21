# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime


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

    state = fields.Selection(
        string='State',
        selection=[('na', 'N/A'),
                   ('active', 'Active'), ('expired', 'Expired')],
        required=False, )

    @api.model
    def create(self, vals):
        if 'expiry_date' in vals and vals['expiry_date']:
            expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d")
            if expiry_date > datetime.today().date():
                vals['state'] = 'active'
            else:
                vals['state'] = 'expired'
        else:
            vals['state'] = 'na'
        return super(ContactDocument, self).create(vals)

    def write(self, vals):
        expiry_date = None
        state = ""
        if 'expiry_date' in vals:
            expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d").date()
        else:
            expiry_date = self.expiry_date

        if 'state' in vals:
            state = vals['state']
        else:
            state = self.state

        if state == 'active':
            if expiry_date:
                if expiry_date < datetime.today().date():
                    raise ValidationError(_("Cannot Edit, check expiry date."))
            else:
                raise ValidationError(_("Status must be N/A"))
        if state == 'expired':
            if expiry_date:
                if expiry_date > datetime.today().date():
                    raise ValidationError(_("Cannot Edit, check expiry date."))
            else:
                raise ValidationError(_("Status must be N/A"))
        if state == 'na':
            if expiry_date:
                raise ValidationError(_("Must not have expiry date"))

        return super(ContactDocument, self).write(vals)



