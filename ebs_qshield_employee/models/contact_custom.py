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
    employee_ids = fields.One2many('hr.employee', 'partner_id', string="Related Employee", auto_join=True)
    is_qshield_sponsor = fields.Boolean(string='Is Qshield Sponsor', compute='_compute_is_qshield_sponsor', store=True)
    check_qshield_sponsor = fields.Boolean(compute="compute_check_qshield_sponsor")
    is_address = fields.Boolean(string="Is Address", default=False)
    is_employee_create = fields.Boolean(string='Is Employee Create')
    job_id = fields.Many2one(comodel_name="hr.job", string="Job Position", required=False, )
    is_work_permit = fields.Boolean(string="Work Permit")
    no_longer_sponsored = fields.Boolean(compute='_compute_no_longer_sponsored')

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

    @api.depends('employee_ids', 'is_qshield_sponsor')
    def _compute_no_longer_sponsored(self):
        for rec in self:
            rec.no_longer_sponsored = True if rec.employee_ids and not rec.is_qshield_sponsor and rec.person_type == 'emp' \
                else False

    @api.onchange('sponsor')
    def _check_contact_employee_validation(self):
        for rec in self:
            if not rec.is_qshield_sponsor and rec.employee_ids:
                warning = {
                    'title': "Warning",
                    'message': "Please validate and update the related employee record accordingly",
                }
                return {'warning': warning}

    @api.depends('sponsor', 'sponsor.is_employee_create', 'sponsor.is_work_permit', 'parent_id',
                 'parent_id.is_employee_create', 'person_type')
    def _compute_is_qshield_sponsor(self):
        for rec in self:
            if rec.person_type == 'emp' and rec.sponsor and (rec.sponsor.is_employee_create or \
                                                             (rec.sponsor.is_work_permit and \
                                                              rec.parent_id and rec.parent_id.is_employee_create)):
                rec.is_qshield_sponsor = True
            else:
                rec.is_qshield_sponsor = False

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
        res = super(ContactCustom, self).write(vals)
        if self.is_qshield_sponsor and self.person_type == 'emp':
            employee_update_dict = {}
            related_employees = self.employee_ids or \
                                self.env['hr.employee'].search([('partner_id', 'in', self.ids), ('active', '=', False)])

            if self.active and not related_employees:
                self.create_employee()
                return res

            if vals.get('active') or 'active' in vals or False in related_employees.mapped('active'):
                employee_update_dict.update({
                    'active': True if False in related_employees.mapped('active') and \
                                      not vals.get('active') else vals.get('active')
                })

            if vals.get('name'):
                partner_name_list = vals.get('name').split()
                first_name = partner_name_list[0]
                middle_name = ' '.join(partner_name_list[1:-1]) if len(partner_name_list) > 2 else ''
                last_name = partner_name_list[-1] if len(partner_name_list) >= 2 else ''
                employee_update_dict.update({
                    'name': vals.get('name'),
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'last_name': last_name})

            if vals.get('nationality'):
                employee_update_dict.update({
                    'country_id': vals.get('nationality'),
                })

            if vals.get('gender'):
                employee_update_dict.update({
                    'gender': vals.get('gender'),
                })

            if vals.get('date'):
                employee_update_dict.update({
                    'birthday': vals.get('date'),
                })

            if vals.get('phone'):
                employee_update_dict.update({
                    'work_phone': vals.get('phone'),
                })

            if vals.get('mobile'):
                employee_update_dict.update({
                    'mobile_phone': vals.get('mobile'),
                })

            if vals.get('email'):
                employee_update_dict.update({
                    'work_email': vals.get('email'),
                })

            if vals.get('sponsor'):
                employee_update_dict.update({
                    'work_in': vals.get('sponsor'),
                })

            if vals.get('iban_number'):
                employee_update_dict.update({
                    'iban_number': vals.get('iban_number'),
                })

            if vals.get('joining_date'):
                employee_update_dict.update({
                    'joining_date': vals.get('joining_date'),
                })

            if vals.get('job_id'):
                job_id = self.env['hr.job'].browse(int(vals.get('job_id')))
                employee_update_dict.update({
                    'job_title': job_id.name,
                    'job_id': vals.get('job_id'),
                })

            if vals.get('sponsor') or vals.get('parent_id'):
                employee_update_dict.update({
                    'is_out_sourced': True if (
                            self.sponsor != self.parent_id and not self.sponsor.is_work_permit) else False,
                })

            if vals.get('parent_id'):
                employee_update_dict.update({
                    'related_company_id': vals.get('parent_id'),
                })

            if vals.get('passport_doc'):
                passport_document_id = self.env['documents.document'].browse(int(vals.get('passport_doc')))
                employee_update_dict.update({
                    'passport_id': passport_document_id.document_number,
                })

            if vals.get('qatar_id_doc'):
                qatar_document_id = self.env['documents.document'].browse(int(vals.get('qatar_id_doc')))
                employee_update_dict.update({
                    'qid_number': qatar_document_id.document_number,
                })

            related_employees.update(employee_update_dict)
        return res

    def create_update_employee(self):
        for rec in self:
            if rec.is_qshield_sponsor:
                partner_name_list = rec.name.split()
                first_name = partner_name_list[0]
                middle_name = ' '.join(partner_name_list[1:-1]) if len(partner_name_list) > 2 else ''
                last_name = partner_name_list[-1] if len(partner_name_list) >= 2 else ''
                vals = {
                    'name': rec.name,
                    'first_name': first_name,
                    'middle_name': middle_name,
                    'last_name': last_name,
                    'country_id': rec.nationality.id,
                    'gender': rec.gender,
                    'birthday': rec.date,
                    'work_phone': rec.phone,
                    'mobile_phone': rec.mobile,
                    'work_email': rec.email,
                    'partner_id': rec.id,
                    'work_in': rec.sponsor.id,
                    'job_title': rec.job_id.name if rec.job_id else False,
                    'iban_number': rec.iban_number,
                    'joining_date': rec.date_join,
                    'is_out_sourced': True if rec.sponsor != rec.parent_id and not rec.sponsor.is_work_permit else False,
                    'related_company_id': rec.parent_id.id if rec.parent_id else False,
                    'passport_id': rec.passport_doc.document_number if rec.passport_doc else False,
                    'qid_number': rec.qatar_id_doc.document_number if rec.qatar_id_doc else False,
                    'job_id': rec.job_id.id if rec.job_id else False,
                }
                if not rec.employee_ids:
                    self.env['hr.employee'].create(vals)
                else:
                    rec.employee_ids.update(vals)

    @api.constrains('employee_dependants')
    def _update_related_employees_dependents(self):

        dependants_list = []
        all_deleted_dependant = self.env['res.partner']

        for rec in self:

            if rec.is_qshield_sponsor:

                for employee in rec.employee_ids:

                    new_dependant = rec.employee_dependants - employee.dependant_id.related_partner_id
                    deleted_dependant = employee.dependant_id.related_partner_id - rec.employee_dependants
                    all_deleted_dependant += deleted_dependant

                    for dependant in new_dependant:
                        dependants_list.append({
                            'hr_employee': employee.id,
                            'related_partner_id': dependant.id,
                        })

        all_deleted_dependant.unlink()
        self.env['hr.dependant'].create(dependants_list)
