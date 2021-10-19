# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class EmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    first_name = fields.Char()
    middle_name = fields.Char()
    last_name = fields.Char()
    partner_id = fields.Many2one('res.partner', string='Related Contact', index=True)
    religion_id = fields.Many2one('hr.religion', string='Religion', index=True)
    dependant_id = fields.One2many('hr.dependant', 'hr_employee', string='Dependants', index=True)
    emergency_id = fields.One2many('hr.emergency', 'hr_employee', string='Emergency', index=True)
    education_id = fields.One2many('hr.education', 'hr_employee', string='School/College/University', index=True)
    courses_id = fields.One2many('hr.courses', 'hr_employee', string='Courses', index=True)
    language_id = fields.One2many('hr.language', 'hr_employee', string='Language', index=True)
    history_id = fields.One2many('hr.history', 'hr_employee', string='Employment History', index=True)
    home_leave_destination = fields.Many2one(comodel_name='res.country', string='Home Leave Destination')
    # nearest_land_mark = fields.Char()
    # fax_number = fields.Char('Fax No.')
    address_home_country = fields.Many2one(
        'res.partner', 'Address (Home Country)',
        help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user", tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    def employee_information_form(self):
        return self.env.ref('ebs_qshield_employee.action_employee_information_form').report_action(self)


class Religion(models.Model):
    _name = 'hr.religion'

    name = fields.Char()


class Dependant(models.Model):
    _name = 'hr.dependant'

    name = fields.Char()
    gender = fields.Selection(string='Sex',
                              selection=[
                                  ('male', 'Male'),
                                  ('female', 'Female')],
                              store=True)
    dob = fields.Date('Date of Birth')
    accompany = fields.Boolean('Are they accompanying you?')
    relation = fields.Selection(string='Relationship',
                                selection=[
                                    ('Spouse', 'Spouse'),
                                    ('Child', 'Child')],
                                store=True)
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class Emergency(models.Model):
    _name = 'hr.emergency'

    name = fields.Char()
    relation = fields.Char('Relationship')
    address = fields.Char()
    telephone = fields.Char('Telephone No.')
    mobile = fields.Char('Mobile No.')
    fax = fields.Char()
    location = fields.Selection(string='Location',
                                selection=[
                                    ('qatar', 'Qatar'),
                                    ('home_country', 'Home Country')],
                                store=True)
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class SchoolCollegeUniversity(models.Model):
    _name = 'hr.education'

    year = fields.Char()
    degree = fields.Float()
    school_college = fields.Char()
    university = fields.Char()
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class Courses(models.Model):
    _name = 'hr.courses'

    from_date = fields.Date('From')
    to_date = fields.Date('To')
    course_title = fields.Char()
    institution = fields.Char('Institution/Address')
    qualification = fields.Char()
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class Language(models.Model):
    _name = 'hr.language'

    name = fields.Char()
    spoken = fields.Char()
    oral = fields.Char()
    written = fields.Char()
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class History(models.Model):
    _name = 'hr.history'

    position = fields.Char()
    company_institution = fields.Char('Company/Institution')
    date = fields.Date()
    hr_employee = fields.Many2one('hr.employee', readonly=True)
