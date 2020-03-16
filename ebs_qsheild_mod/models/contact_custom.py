# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ContactCustom(models.Model):
    _inherit = 'res.partner'
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
        required=True, default='company')

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

    account_manager = fields.Many2one(
        comodel_name='hr.employee',
        string='Account Manager',
        required=False)
    related_parent = fields.Many2one(
        comodel_name='res.partner',
        string='Parent',
        required=False,
        domain=[('person_type', '=', 'emp')])

    related_contacts = fields.One2many(
        comodel_name='res.partner',
        inverse_name='parent_id',
        string='Related Contacts',
        required=False
    )

    dependents = fields.One2many(
        comodel_name='res.partner',
        inverse_name='related_parent',
        string='Dependents',
        required=False)
    contracts = fields.One2many(
        comodel_name='ebs_mod.contracts',
        inverse_name='contact_id',
        string='Contracts',
        required=False)

    documents = fields.One2many(
        comodel_name='ebs_mod.contact.document',
        inverse_name='contact_id',
        string='Documents',
        required=False)

    def sponsor_domain(self):
        if self.person_type == 'company':
            return [('person_type', '=', 'company')]
        if self.person_type == 'emp' or self.person_type == 'visitor':
            return [('person_type', '=', 'company')]
        if self.person_type == 'child':
            return ['|', ('person_type', '=', 'emp'), ('person_type', '=', 'company')]

    @api.depends('related_parent', 'parent_id')
    def _sponsor_default(self):
        if self.person_type == 'company':
            return self.id
        if self.person_type == 'emp' or self.person_type == 'visitor':
            return self.parent_id.id
        if self.person_type == 'child':
            return self.related_parent.id
        return None

    sponsor = fields.Many2one(
        comodel_name='res.partner',
        string='Sponsor',
        required=False,
        default=_sponsor_default,
        domain=sponsor_domain)

    @api.depends('is_company', 'name', 'parent_id.name', 'type', 'company_name')
    @api.depends_context('show_address', 'show_address_only', 'show_email', 'html_format', 'show_vat')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name

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
                    if vals['person_type'] == 'visitor' or vals['person_type'] == 'emp':
                        if res.parent_id:
                            res.sponsor = res.parent_id.id
                    if vals['person_type'] == 'child':
                        if res.related_parent:
                            res.sponsor = res.related_parent.id
        return res

    def write(self, vals):
        if 'person_type' in vals:
            if self.person_type == "visitor" and vals['person_type'] == "emp":
                self.message_post(body="Type Changed From Visitor to Employee")
        res = super(ContactCustom, self).write(vals)

        return res

#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100
