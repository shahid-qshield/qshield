# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    parent_id = fields.Many2one('res.partner', string='Related Contact', index=True)

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

    nationality = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        required=False)
    passport_id = fields.Char(
        string='Passport ID',
        required=False)
    passport_exp_date = fields.Date(
        string='Passport Expiry Date',
        required=False)
    qatar_id = fields.Char(
        string='Qatar ID',
        required=False)
    qatarid_exp_date = fields.Date(
        string='Qatar ID Expiry Date',
        required=False)
    computer_card_number = fields.Char(
        string='Computer Card Number',
        required=False)
    comp_card_exp_date = fields.Date(
        string='Computer Card Expiry Date',
        required=False)

    cr_number = fields.Char(
        string='CR Number',
        required=False)
    cr_exp_date = fields.Date(
        string='CR Expiry Date',
        required=False)

    trade_licence_number = fields.Char(
        string='Trade Licence Number',
        required=False)
    trade_licence_date = fields.Date(
        string='Trade Licence Expiry Date',
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

    def sponsor_domain(self):
        if self.person_type == 'company':
            return [('person_type', '=', 'company')]
        if self.person_type == 'emp' or self.person_type == 'visitor':
            return [('person_type', '=', 'company')]
        if self.person_type == 'child':
            return ['|', ('person_type', '=', 'emp'), ('person_type', '=', 'company')]

    @api.depends('parent_id')
    def _sponsor_default(self):
        if self.person_type == 'company':
            return self.id
        if self.person_type in ('emp', 'child', 'visitor'):
            return self.parent_id.id
        return None

    sponsor = fields.Many2one(
        comodel_name='res.partner',
        string='Sponsor',
        required=False,
        default=_sponsor_default,
        domain=sponsor_domain)

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

        return {
            'domain': {
                'sponsor': self.sponsor_domain()
            }
        }

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
                    if vals['person_type'] in ('visitor', 'emp', 'child'):
                        if res.parent_id:
                            res.sponsor = res.parent_id.id
        return res

    def write(self, vals):
        if 'person_type' in vals:
            if self.person_type == "visitor" and vals['person_type'] == "emp":
                self.message_post(body="Type Changed From Visitor to Employee")
        res = super(ContactCustom, self).write(vals)

        return res

    def _get_name(self):
        if self.person_type:
            return self.name
        else:
            return super(ContactCustom, self)._get_name()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
