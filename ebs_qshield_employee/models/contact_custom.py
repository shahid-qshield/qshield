# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    nearest_land_mark = fields.Char()
    fax_number = fields.Char('Fax No.')
    # employee_id = fields.Many2one('hr.employee', string='Related Employee', index=True)
    employee_ids = fields.One2many('hr.employee', 'partner_id', string="Related Employee", auto_join=True)
    is_qshield_sponsor = fields.Boolean(string='Is Qshield Sponsor')
    check_qshield_sponsor = fields.Boolean(compute="compute_check_qshield_sponsor")
    is_address = fields.Boolean(string="Is Address", default=False)

    @api.depends('sponsor', 'person_type')
    def compute_check_qshield_sponsor(self):
        for rec in self:
            if rec.sponsor and rec.sponsor.is_qshield_sponsor and rec.person_type == 'emp':
                rec.check_qshield_sponsor = True
            else:
                rec.check_qshield_sponsor = False

    @api.constrains('employee_ids')
    def _check_employee_length(self):
        for contact in self:
            if len(contact.employee_ids) > 1:
                raise ValidationError(
                    _('Only one employee link with contact'))

    @api.model
    def create(self, values):
        # Add code here
        res = super(ContactCustom, self).create(values)
        if self._context.get('from_employee'):
            return res
        else:
            if res.person_type == 'emp':
                res.create_employee()
            return res

    def create_employee(self):
        for rec in self:
            if not rec.employee_ids:
                dependants = []
                for each_dependant in rec.employee_dependants:
                    dependants.append((0, 0, {
                        'name': each_dependant.name,
                        'gender': each_dependant.gender,
                        'dob': each_dependant.date,
                    }))
                employee = self.env['hr.employee'].create({
                    'name': rec.name,
                    'country_id': rec.nationality.id,
                    'gender': rec.gender,
                    'birthday': rec.date,
                    # 'job_id': rec.function,
                    'work_phone': rec.phone,
                    'mobile_phone': rec.mobile,
                    'work_email': rec.email,
                    'dependant_id': dependants,
                    'partner_id': rec.id,
                    'work_in': rec.sponsor.id,
                })
                # rec.employee_id = employee
