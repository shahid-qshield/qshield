# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import os
import xlrd


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    nearest_land_mark = fields.Char()
    fax_number = fields.Char('Fax No.')
    # employee_id = fields.Many2one('hr.employee', string='Related Employee', index=True)
    employee_ids = fields.One2many('hr.employee', 'partner_id', string="Related Employee", auto_join=True,
                                   domain="[('active', '=', True and False)]")
    is_qshield_sponsor = fields.Boolean(string='Is Qshield Sponsor')
    check_qshield_sponsor = fields.Boolean(compute="compute_check_qshield_sponsor")
    is_address = fields.Boolean(string="Is Address", default=False)

    def update_invoice_type(self):
        file_path = os.path.dirname(os.path.dirname(__file__)) + '/data/Company Types.xlsx'
        with open(file_path, 'rb') as f:
            try:
                workbook = xlrd.open_workbook(file_path, on_demand=True)
                worksheet = workbook.sheet_by_index(0)
                first_row = []
                for col in range(worksheet.ncols):
                    first_row.append(worksheet.cell_value(0, col))
                data = []
                for row in range(1, worksheet.nrows):
                    elm = {}
                    for col in range(worksheet.ncols):
                        elm[first_row[col]] = worksheet.cell_value(row, col)
                    data.append(elm)
                for rec in data:
                    partner = self.sudo().search([('name', 'ilike', rec.get('Name')), ('active', 'in', [False, True])])
                    if partner:
                        if rec.get('Company Type') and rec.get('Company Type').capitalize() == 'Per transaction':
                            partner.write({'partner_invoice_type': 'per_transaction'})
                        elif rec.get('Company Type') and rec.get('Company Type').capitalize() == 'Retainer':
                            partner.write({'partner_invoice_type': 'retainer'})
                        elif rec.get('Company Type') and rec.get('Company Type').capitalize() == 'Partner':
                            partner.write({'partner_invoice_type': 'partners'})
                        elif rec.get('Company Type') and rec.get('Company Type').capitalize() == 'Outsourcing':
                            partner.write({'partner_invoice_type': 'outsourcing'})
                        elif rec.get('Company Type') and rec.get('Company Type').capitalize() == 'One time transaction':
                            partner.write({'partner_invoice_type': 'one_time_transaction'})
                        elif rec.get('Company Type') and rec.get(
                                'Company Type').capitalize() == 'Retainer, outsourcing':
                            partner.write({'partner_invoice_type': 'retainer'})
                        elif rec.get('Company Type') and rec.get('Company Type').capitalize() == "Please archive":
                            if partner.active:
                                partner.active = False
            except Exception as e:
                raise UserError(e)

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

    def write(self, vals):
        if self.person_type == 'company':
            all_related_partner = self.env['res.partner'].sudo().search(
                [('sponsor', '=', self.id), ('person_type', '=', 'emp')])
            for partners in all_related_partner:
                if not vals.get('is_qshield_sponsor'):
                    if partners.employee_ids:
                        partners.employee_ids.write({'active': False})
                if vals.get('is_qshield_sponsor'):
                    employee = partners.employee_ids.search([('active', '=', False), ('name', '=', partners.name)],
                                                            limit=1)
                    if employee:
                        employee.write({'active': True})
                        partners.employee_ids.write({'partner_id': [(4, partners.id)]})
                    else:
                        partners.create_employee(partner=partners)

        elif vals.get('sponsor') or vals.get('person_type') == 'emp' or self.person_type == 'emp':
            new_sponsor = False
            if not self.employee_ids:
                employee = self.employee_ids.filtered(lambda a: not a.active)
                if employee:
                    employee.write({'active': True})
                    self.employee_ids.partner_id = self.id
                else:
                    if vals.get('sponsor'):
                        new_sponsor = self.env['res.partner'].sudo().browse(vals.get('sponsor'))
                    self.create_employee(sponsor=new_sponsor)
            new_sponsor = self.env['res.partner'].sudo().browse(vals.get('sponsor'))
            if new_sponsor and not new_sponsor.is_qshield_sponsor:
                if self.employee_ids:
                    self.employee_ids.write({'active': False})
        if self.person_type == 'emp' and vals.get('person_type') in ['company', 'child', 'visitor']:
            if self.employee_ids:
                self.employee_ids.write({'active': False})
        return super(ContactCustom, self).write(vals)

    def create_employee(self, partner=False, sponsor=False):
        for rec in self:
            dependants = []
            if partner:
                if not partner.employee_ids:
                    for each_dependant in partner.employee_dependants:
                        dependants.append((0, 0, {
                            'name': each_dependant.name,
                            'gender': each_dependant.gender,
                            'dob': each_dependant.date,
                        }))
                    employee = self.env['hr.employee'].create({
                        'name': partner.name,
                        'country_id': partner.nationality.id,
                        'gender': partner.gender,
                        'birthday': partner.date,
                        # 'job_id': rec.function,
                        'work_phone': partner.phone,
                        'mobile_phone': partner.mobile,
                        'work_email': partner.email,
                        'dependant_id': dependants,
                        'partner_id': partner.id,
                        'work_in': partner.sponsor.id,
                    })
                    print("Create EMP -", employee.name)
                elif partner.employee_ids[0].active:
                    partner.employee_ids.update({'partner_id': partner.id})
            else:
                if sponsor and sponsor.is_qshield_sponsor or rec.sponsor.is_qshield_sponsor:
                    if not rec.employee_ids:
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
