# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    _sql_constraints = [
        ('person_type_name_parent_unique', 'unique (person_type, parent_id,name)',
         'The combination of Type, Related Contact and Name must be unique !'),
    ]

    parent_id = fields.Many2one('res.partner', string='Related Contact', index=True)
    date_stop_renew = fields.Date(
        string='Do Not Renew After',
        required=False)
    is_miscellaneous = fields.Boolean(
        string='Is Miscellaneous',
        required=False, default=False)
    gender = fields.Selection(
        string='Gender',
        selection=[('male', 'Male'),
                   ('female', 'Female'), ],
        required=False, )
    person_type = fields.Selection(
        string='Person Type',
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
    )
    date_join = fields.Date(
        string='join Date',
        required=False)

    date_termination = fields.Date(
        string='Termination Date',
        required=False)

    nationality = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        required=False)

    passport_doc = fields.Many2one(
        comodel_name='documents.document',
        string='Passport Document',
        required=False
    )
    # passport_id = fields.Char(
    #     related='passport_doc.document_number',
    #     string='Passport ID',
    #     required=False)
    passport_exp_date = fields.Date(
        related='passport_doc.expiry_date',
        string='Passport Expiry Date',
        required=False)

    qatar_id_doc = fields.Many2one(
        comodel_name='documents.document',
        string='Qatar ID Document',
        required=False
    )

    # qatar_id = fields.Char(
    #     #     string='Qatar ID',
    #     #     required=False)

    qatarid_exp_date = fields.Date(
        string='Qatar ID Expiry Date', related='qatar_id_doc.expiry_date',
        required=False)

    computer_card_doc = fields.Many2one(
        comodel_name='documents.document',
        string='Computer Card Document',
        required=False
    )

    # computer_card_number = fields.Char(
    #     string='Computer Card Number',
    #     required=False)
    comp_card_exp_date = fields.Date(
        string='Computer Card Expiry Date', related='computer_card_doc.expiry_date',
        required=False)

    cr_number_doc = fields.Many2one(
        comodel_name='documents.document',
        string='CR Number Document',
        required=False
    )

    # cr_number = fields.Char(
    #     string='CR Number',
    #     required=False)
    cr_exp_date = fields.Date(
        string='CR Expiry Date', related='cr_number_doc.expiry_date',
        required=False)

    trade_licence_doc = fields.Many2one(
        comodel_name='documents.document',
        string='Trade Licence Document',
        required=False
    )

    # trade_licence_number = fields.Char(
    #     string='Trade Licence Number',
    #     required=False)
    trade_licence_date = fields.Date(
        string='Trade Licence Expiry Date', related='trade_licence_doc.expiry_date',
        required=False)

    account_manager = fields.Many2one(
        comodel_name='hr.employee',
        string='Account Manager',
        required=False)

    company_visitors = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_id',
        string='Related Visitors',
        required=False, domain=[('person_type', '=', 'visitor')]
    )

    company_employees = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_id',
        string='Related Employees',
        required=False, domain=[('person_type', '=', 'emp')]
    )

    employee_dependants = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_id',
        string='Related Dependants',
        required=False, domain=[('person_type', '=', 'child')]
    )
    sponsor_for = fields.One2many(
        comodel_name='res.partner',
        inverse_name='sponsor',
        string='Sponsor For',
        required=False, readonly=True
    )
    contracts = fields.One2many(
        comodel_name='ebs_mod.contracts',
        inverse_name='contact_id',
        string='Contracts',
        required=False)

    document_o2m = fields.One2many(
        comodel_name='documents.document',
        inverse_name='partner_id',
        string='Related Documents',
        required=False)

    service_ids = fields.One2many(
        comodel_name='ebs_mod.service.request',
        inverse_name='partner_id',
        string='Services',
        required=False)

    def _get_service_count(self):
        for rec in self:
            rec.service_count = len(rec.service_ids)

    service_count = fields.Integer(
        string='Services Count',
        required=False,
        compute="_get_service_count")

    # document_o2m_archived = fields.One2many(
    #     comodel_name='documents.document',
    #     inverse_name='partner_id',
    #     string='Related Documents Archived',
    #     required=False, compute="_get_archived_documents",
    # )
    #
    # def _get_archived_documents(self):
    #     for rec in self:
    #         ids = []
    #         # for doc in self.env['documents.document'].with_context(active_test=False).search(
    #         #         [('partner_id', '=', rec.id), ('active', '=', False)]):
    #         #     ids.append(doc.id)
    #         rec.document_o2m_archived = self.env['documents.document'].with_context(active_test=False).search(
    #             [('partner_id', '=', rec.id), ('active', '=', False)])

    # def sponsor_domain(self):
    #     if self.person_type == 'company':
    #         return [('person_type', '=', 'company')]
    #     if self.person_type == 'emp' or self.person_type == 'visitor':
    #         return [('person_type', '=', 'company')]
    #     if self.person_type == 'child':
    #         return ['|', ('person_type', '=', 'emp'), ('person_type', '=', 'company')]

    @api.depends('parent_id')
    def _sponsor_default(self):
        if self.person_type == 'company':
            return self.id
        if self.person_type in ('emp', 'visitor'):
            return self.parent_id.id
        if self.person_type == 'child':
            self.sponsor = self.parent_id.parent_id.id
        return None

    @api.depends('parent_id')
    def _sponsor_compute(self):
        for rec in self:
            if rec.person_type == 'company':
                if 'default_sponsor' in rec._context:
                    if rec._context['default_sponsor']:
                        rec.sponsor = rec._context['default_sponsor']
                else:
                    rec.sponsor = rec.id
            if rec.person_type == 'visitor' or rec.person_type == 'emp':
                if 'default_sponsor' in rec._context:
                    if rec._context['default_sponsor']:
                        rec.sponsor = rec._context['default_sponsor']
                else:
                    rec.sponsor = rec.parent_id.id
            if rec.person_type == 'child':
                if 'default_sponsor' in rec._context:
                    if rec._context['default_sponsor']:
                        rec.sponsor = rec._context['default_sponsor']
                else:
                    rec.sponsor = rec.parent_id.sponsor.id

    sponsor = fields.Many2one(
        comodel_name='res.partner',
        string='Sponsor',
        required=False,
        readonly=False,
        default=_sponsor_default,
        # compute='_sponsor_compute', store=True,
        domain=[('person_type', '=', 'company')])

    @api.depends('parent_id')
    def _get_related_company(self):
        for rec in self:
            if rec.person_type == 'child':
                rec.related_company = rec.parent_id.parent_id.id
            if rec.person_type in ('emp', 'visitor'):
                rec.related_company = rec.parent_id.id

    related_company = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        required=False,
        store=True,
        compute='_get_related_company')

    dependants = fields.One2many(
        comodel_name='res.partner',
        inverse_name='related_company',
        string='Dependants',
        domain=[('person_type', '=', 'child')],
        required=False, readonly=True)

    contact_relation_type_id = fields.Many2one(
        comodel_name='ebs_mod.contact.relation.type',
        string='Relation Type',
        required=False)

    payment_ids = fields.One2many(
        comodel_name='ebs_mod.contact.payment',
        inverse_name='partner_id',
        string='Payments',
        required=False)

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name')
    @api.depends_context('show_address', 'show_address_only', 'show_email', 'html_format', 'show_vat')
    def _compute_display_name(self):
        # if partner.person_type in ('emp', 'visitor', 'child'):
        diff = dict(show_address=None, show_address_only=None, show_email=None, html_format=None, show_vat=None)
        names = dict(self.with_context(**diff).name_get())
        for partner in self:
            if partner.person_type:
                partner.display_name = partner.name
            else:
                partner.display_name = names.get(partner.id)

    @api.onchange('person_type')
    def _person_type_change(self):
        if self.person_type == 'company':
            self.company_type = 'company'
        else:
            self.company_type = 'person'

        # return {
        #     'domain': {
        #         'sponsor': self.sponsor_domain()
        #     }
        # }

    @api.model
    def create(self, vals):
        res = super(ContactCustom, self).create(vals)
        if res:
            bool_create_sponsor = False
            if 'sponsor' not in vals:
                bool_create_sponsor = True
            else:
                if not vals['sponsor']:
                    bool_create_sponsor = True
            if bool_create_sponsor:
                if 'person_type' in vals:
                    if vals['person_type'] == 'company':
                        res.sponsor = res.id
                    if vals['person_type'] in ('visitor', 'emp'):
                        if res.parent_id:
                            res.sponsor = res.parent_id.id
                    if vals['person_type'] == 'child':
                        if res.parent_id.sponsor:
                            res.sponsor = res.parent_id.sponsor.id
        return res

    def write(self, vals):
        if 'person_type' in vals:
            if self.person_type == "visitor" and vals['person_type'] == "emp":
                self.message_post(body="Type Changed From Visitor to Employee")

        if vals.get('parent_id', False):
            new_res = self.env['res.partner'].browse(vals['parent_id'])
            for rec in self.employee_dependants:
                rec.related_company = new_res.id
                rec.sponsor = new_res.sponsor.id
            self.message_post(
                body="Related contact changed from '" + self.parent_id.name + "' to '" + new_res.name + "'")

        active_before = self.active
        res = super(ContactCustom, self).write(vals)
        active_after = self.active
        if active_after != active_before:
            self.contact_archive_onchange(active_after)
        return res

    def contact_archive_onchange(self, active):
        self.contact_document_archive(active)
        related_contacts_list = self.env['res.partner'].search(
            [('parent_id', '=', self.id), ('active', '=', (not active))])
        for rec in related_contacts_list:
            rec.active = active

    def contact_document_archive(self, active):
        document_list = self.env['documents.document'].search(
            [('partner_id', '=', self.id), ('active', '=', (not active))])
        for rec in document_list:
            rec.active = active

    def _get_name(self):
        if self.person_type:
            return self.name
        else:
            return super(ContactCustom, self)._get_name()

    def unlink(self):
        for rec in self:
            if rec.person_type == 'company':
                if len(rec.company_visitors) > 0 or len(rec.company_employees) > 0:
                    raise ValidationError(_("Cannot delete, check linked items"))
            if rec.person_type == 'emp':
                if len(rec.employee_dependants) > 0:
                    raise ValidationError(_("Cannot delete, check linked items"))

            for doc in rec.document_o2m:
                doc.unlink()
            super(ContactCustom, rec).unlink()

    @api.onchange('parent_id')
    def onchange_parent_id(self):
        # return values in result, as this method is used by _fields_sync()
        if not self.parent_id:
            return
        result = {}
        partner = self._origin
        # if partner.parent_id and partner.parent_id != self.parent_id:
        #     result['warning'] = {
        #         'title': _('Warning'),
        #         'message': _('Changing the company of a contact should only be done if it '
        #                      'was never correctly set. If an existing contact starts working for a new '
        #                      'company then a new contact should be created under that new '
        #                      'company. You can use the "Discard" button to abandon this change.')}
        if partner.type == 'contact' or self.type == 'contact':
            # for contacts: copy the parent address, if set (aka, at least one
            # value is set in the address: otherwise, keep the one from the
            # contact)
            address_fields = self._address_fields()
            if any(self.parent_id[key] for key in address_fields):
                def convert(value):
                    return value.id if isinstance(value, models.BaseModel) else value

                result['value'] = {key: convert(self.parent_id[key]) for key in address_fields}
        return result

    @api.depends('person_type')
    @api.onchange('parent_id')
    def parent_id_onchange(self):
        if self.person_type == 'visitor' or self.person_type == 'emp':
            self.sponsor = self.parent_id.id
        if self.person_type == 'child':
            self.sponsor = self.parent_id.parent_id.id
            self.nationality = self.parent_id.nationality.id

    #
    #     @api.depends('value')
    #     def _value_pc(self):
    #         self.value2 = float(self.value) / 100
    def action_see_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
            'view_mode': 'kanban',
            'context': {
                "search_default_partner_id": self.id,
                "default_partner_id": self.id,
                "searchpanel_default_folder_id": False,
                "hide_contact": True,
                "hide_service": True
            },
        }

    def action_see_services(self):
        self.ensure_one()
        return {
            'name': _('Service Request'),
            'res_model': 'ebs_mod.service.request',
            'type': 'ir.actions.act_window',
            'views': [(False, 'tree'), (False, 'form')],
            'view_mode': 'tree',
            'context': {
                "search_default_partner_id": self.id,
                "default_partner_id": self.id,
            },
        }
