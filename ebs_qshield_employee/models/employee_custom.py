# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeCustom(models.Model):
    _inherit = 'hr.employee'

    first_name = fields.Char()
    middle_name = fields.Char()
    last_name = fields.Char()
    driving_license = fields.Boolean('Driving License')
    qid_number = fields.Char('QID Number')
    country_issue = fields.Many2one(comodel_name='res.country', string='Country of Issue')
    partner_id = fields.Many2one('res.partner', string='Related Contact', index=True)
    work_in = fields.Many2one('res.partner', string='Work In')
    religion_id = fields.Many2one('hr.religion', string='Religion', index=True)
    religion = fields.Selection(string='Religion',
                                selection=[
                                    ('christianity', 'Christianity'),
                                    ('islam', 'Islam'),
                                    ('atheist', 'Atheist'),
                                    ('hinduism', 'Hinduism'),
                                    ('Buddhism', 'Buddhism'),
                                    ('chinese_traditional_religion', 'Chinese traditional religion'),
                                    ('ethnic_religions', 'Ethnic religions'),
                                    ('african_traditional_religions', 'African traditional religions'),
                                    ('sikhism', 'Sikhism'),
                                    ('spiritism', 'Spiritism'),
                                    ('judaism', 'Judaism'),
                                    ('baháʼí', 'Baháʼí'),
                                    ('jainism', 'Jainism'),
                                    ('shinto', 'Shinto'),
                                    ('cao_dai', 'Cao Dai'),
                                    ('zoroastrianism', 'Zoroastrianism'),
                                    ('tenrikyo', 'Tenrikyo'),
                                    ('animism', 'Animism'),
                                    ('neo-paganism', 'Neo-Paganism'),
                                    ('unitarian_universalism', 'Unitarian Universalism'),
                                    ('rastafari', 'Rastafari')],
                                store=True)
    dependant_id = fields.One2many('hr.dependant', 'hr_employee', string='Dependants', index=True)
    emergency_id = fields.One2many('hr.emergency', 'hr_employee', string='Emergency', index=True)
    education_id = fields.One2many('hr.education', 'hr_employee', string='School/College/University', index=True)
    courses_id = fields.One2many('hr.courses', 'hr_employee', string='Courses', index=True)
    language_id = fields.One2many('hr.language', 'hr_employee', string='Language', index=True)
    history_id = fields.One2many('hr.history', 'hr_employee', string='Employment History', index=True)
    home_leave_destination = fields.Many2one(comodel_name='res.country', string='Home Leave Destination')
    address_home_country = fields.Many2one(
        'res.partner', 'Address (Home Country)',
        help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user", tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    is_out_sourced = fields.Boolean(string="Out source ?", default=False)

    joining_date = fields.Date(string="Joining Date", default=lambda self: fields.Datetime.now(), required=True)
    visa = fields.Many2one(comodel_name="visa.status", string="Visa Status", required=False, )
    custom_document_count = fields.Integer(compute="_compute_document_count", store=False)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            employee = self.search([('partner_id', '=', self.partner_id.id)])
            if employee:
                raise ValidationError(_('Partner is already linked with another employee'))

    @api.model
    def create(self, values):
        res = super(EmployeeCustom, self).create(values)
        if not res.partner_id:
            if res.dependant_id:
                dependants = []
                for dependant in res.dependant_id:
                    vals = {'name': dependant.name, 'gender': dependant.gender, 'date': dependant.dob,
                            'person_type': 'child'}
                    dependant = self.env['res.partner'].with_context(from_employee=True).create(vals)
                    dependants.append(dependant)
            partner = self.env['res.partner'].with_context(from_employee=True).create(
                {'name': res.name, 'person_type': 'emp'})
            if partner:
                res.partner_id = partner.id
                for dependant in dependants:
                    dependant.write({'parent_id': partner.id})
        return res

    def _compute_document_count(self):
        for record in self:
            count = 0
            document_count = self.env['documents.document'].search_count(
                [('partner_id', '!=', False), ('partner_id', '=', record.partner_id.id)])
            if document_count:
                count = document_count
            record.custom_document_count = count

    def action_see_own_documents(self):
        action = self.env.ref('ebs_qshield_employee.custom_document_action').read()[0]
        action['domain'] = [('partner_id', '!=', False), ('partner_id', '=', self.partner_id.id)]
        return action

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

    name = fields.Char(required=True)
    relation = fields.Char('Relationship')
    address = fields.Char()
    telephone = fields.Char('Telephone No.')
    mobile = fields.Char('Mobile No.')
    fax = fields.Char()
    location = fields.Selection(string='Location',
                                selection=[
                                    ('qatar', 'Qatar'),
                                    ('home_country', 'Home Country')],
                                store=True, default='home_country')
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
    course_title = fields.Char(required=True)
    institution = fields.Char('Institution/Address')
    qualification = fields.Char()
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class Language(models.Model):
    _name = 'hr.language'

    name = fields.Char(required=True)
    spoken = fields.Char()
    oral = fields.Char()
    written = fields.Char()
    hr_employee = fields.Many2one('hr.employee', readonly=True)


class History(models.Model):
    _name = 'hr.history'

    position = fields.Char(required=True)
    company_institution = fields.Char('Company/Institution')
    date = fields.Date()
    hr_employee = fields.Many2one('hr.employee', readonly=True)
