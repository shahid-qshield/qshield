# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import os
import xlrd
import datetime


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

    # def create_employee_loan(self):
    #     records = pe.get_records(
    #         file_name='/home/tus/workspace/custom/odoo13_custom/qshield_stage/qshield/ebs_qshield_employee/data/qshield_employee_loan.xlsx')
    #     for record in records:
    #         if record.get('Employee name') != '' and record.get('Loan Amount') != '':
    #             employee_id = self.env['hr.employee'].search([('name', '=', record.get('Employee name'))], limit=1)
    #             if not employee_id:
    #                 employee_id = self.env['hr.employee'].create({'name', '=', record.get('Employee name')})
    #             loan_vals = {
    #                 'employee_id': employee_id.id,
    #                 'loan_amount': record.get('Loan Amount'),
    #                 'installment': record.get('No Of Installments'),
    #                 'purpose_of_advance': record.get('Purpose of Advance')
    #             }
    #             if record.get('Department') != '':
    #                 department_id = self.env['hr.department'].search([('name', '=', record.get('Department'))])
    #                 if not department_id:
    #                     department_id = self.env['hr.department'].create({'name': record.get('Department')})
    #                 loan_vals.update({'department_id': department_id.id})
    #             if record.get('Job Position') != '':
    #                 job_position = self.env['hr.job'].search([('name', '=', record.get('Job Position'))])
    #                 if not job_position:
    #                     job_position = self.env['hr.job'].create({'name': record.get('Job Position')})
    #                 loan_vals.update({'job_position': job_position.id})
    #             if record.get('Payment Start Date') != '':
    #                 payment_date = record.get('Payment Start Date').strftime('%Y-%m-%d')
    #                 loan_vals.update({'payment_date': payment_date})
    #             loan = self.env['hr.loan'].sudo().create(loan_vals)
    #             if loan:
    #                 loan.compute_installment()

    def create_contract_of_qshield_employee(self):
        file_path = os.path.dirname(os.path.dirname(__file__)) + '/data/Salaries.xlsx'
        with open(file_path, 'rb') as f:
            try:
                file_data = f.read()
                workbook = xlrd.open_workbook(file_contents=file_data)
                worksheet = workbook.sheet_by_index(0)
                first_row = []
                for col in range(worksheet.ncols):
                    first_row.append(worksheet.cell_value(0, col))
                data = []
                for row in range(1, worksheet.nrows):
                    elm = {}
                    for col in range(worksheet.ncols):
                        if first_row[col] in ['Start Date', 'End Date']:
                            if worksheet.cell_value(row, col) != '':
                                elm[first_row[col]] = xlrd.xldate_as_datetime(worksheet.cell_value(row, col),
                                                                              0).strftime(
                                    '%Y-%m-%d')
                            elif first_row[col] == 'Start Date':
                                first_date_of_year = datetime.datetime.now().replace(day=1, month=1)
                                elm[first_row[col]] = first_date_of_year
                            else:
                                elm[first_row[col]] = ''
                        else:
                            elm[first_row[col]] = worksheet.cell_value(row, col)
                    data.append(elm)
                for record in data:
                    if record.get('Name') != '' and record.get('Employee Name'):
                        employee_id = self.search([('name', 'ilike', record.get('Employee Name'))], limit=1)
                        if employee_id:
                            start_date = False
                            end_date = False
                            department_id = False
                            job_id = False
                            contract_duration = False
                            leave_entitlement = False
                            if record.get('Department') != '':
                                department_id = self.env['hr.department'].search(
                                    [('name', '=', record.get('Department'))], limit=1)
                                if not department_id:
                                    department_id = self.env['hr.department'].create({'name': record.get('Department')})
                            if record.get('End Date') != '':
                                end_date = record.get('End Date')
                            if record.get('Start Date') != '':
                                start_date = record.get('Start Date')
                            if record.get('Job Position') != '':
                                job_id = self.env['hr.job'].search([('name', '=', record.get('Job Position'))], limit=1)
                                if not job_id:
                                    job_id = self.env['hr.job'].create({'name': record.get('Job Position')})
                            if record.get('Contract Duration') != '':
                                contract_duration = record.get('Contract Duration')
                            if record.get('Leave Entitlement') != '':
                                leave_entitlement = record.get('Leave Entitlement')
                            leave_selection = False
                            if record.get('Leave Selection') == 'Calendar Days':
                                leave_selection = 'calendar_days'
                            elif record.get('Leave Selection') == 'Working Days':
                                leave_selection = 'working_days'
                            contract_vals = {
                                'name': record.get('Name'),
                                'employee_id': employee_id.id if employee_id else False,
                                'date_start': start_date,
                                'contract_type': record.get('Contract Type'),
                                'wage': record.get('Wage'),
                                'date_end': end_date,
                                'department_id': department_id.id if department_id else False,
                                'job_id': job_id.id if job_id else False,
                                'contract_duration': contract_duration,
                                'leave_entitlement': leave_entitlement,
                                'leave_selection': leave_selection,
                                'eligible_for_ticket': True if record.get('Eligible For Ticket') == 1 else False,
                                'ticket_period': str(record.get('Ticket Period')) if record.get(
                                    'Ticket Period') != 0 else False
                            }
                            contract = self.env['hr.contract'].search(
                                [('employee_id', '=', employee_id.id), ('date_start', '=', start_date),
                                 ('date_end', '=', end_date)], limit=1)
                            if contract:
                                contract.write(contract_vals)
                            else:
                                contract = self.env['hr.contract'].create(contract_vals)
            except Exception as e:
                print('Something Wrong', e)

    def create_employees(self):
        file_path = os.path.dirname(os.path.dirname(__file__)) + '/data/Employees Record.xlsx'
        with open(file_path, 'rb') as f:
            try:
                file_data = f.read()
                workbook = xlrd.open_workbook(file_contents=file_data)
                worksheet = workbook.sheet_by_index(0)
                first_row = []
                for col in range(worksheet.ncols):
                    first_row.append(worksheet.cell_value(0, col))
                data = []
                for row in range(1, worksheet.nrows):
                    elm = {}
                    for col in range(worksheet.ncols):
                        if first_row[col] in ['Joining Date', 'Date of Birth', 'Spouse Birthdate',
                                              'Visa Expire Date',
                                              'Employment History/Date']:

                            if worksheet.cell_value(row, col) != '':
                                elm[first_row[col]] = xlrd.xldate_as_datetime(worksheet.cell_value(row, col),
                                                                              0).strftime(
                                    '%Y-%m-%d')
                            else:
                                elm[first_row[col]] = False
                        elif first_row[col] in ['Work Mobile', 'Work Phone', 'Private Phone', 'Identification No',
                                                'Passport No', 'Visa No', 'Work Permit No', 'Emergency/Telephone No.',
                                                'Emergency/Mobile No.', 'Emergency/Fax',
                                                'School/College/University/Year']:
                            if isinstance(worksheet.cell_value(row, col), float):
                                elm[first_row[col]] = str(int(worksheet.cell_value(row, col)))
                            else:
                                elm[first_row[col]] = worksheet.cell_value(row, col)
                        else:
                            elm[first_row[col]] = worksheet.cell_value(row, col)
                    data.append(elm)
                for record in data:
                    if record.get('Employee Name') != '':
                        employee = self.search([('name', 'ilike', record.get('Employee Name'))], limit=1)
                        gender = ''
                        if record.get('Gender') == 'Male':
                            gender = 'male'
                        elif record.get('Gender') == 'Female':
                            gender = 'female'
                        marital_status = ''
                        if record.get('Marital Status') == 'Single':
                            marital_status = 'single'
                        elif record.get('Marital Status') == 'Married':
                            marital_status = 'married'
                        elif record.get('Marital Status') == 'Legal Cohabitant':
                            marital_status = 'cohabitant'
                        elif record.get('Marital Status') == 'Widower':
                            marital_status = 'widower'
                        elif record.get('Marital Status') == 'Divorced':
                            marital_status = 'divorced'
                        employee_vals = {
                            'name': record.get('Employee Name'),
                            'first_name': record.get('First Name'),
                            'middle_name': record.get('Middle Name'),
                            'last_name': record.get('Last Name'),
                            'is_out_sourced': True if record.get('Out source ?') == 'Yes' else False,
                            'mobile_phone': record.get('Work Mobile'),
                            'work_phone': record.get('Work Phone'),
                            'work_email': record.get('Work Email'),
                            'work_location': record.get('Work Location'),
                            'driving_license': True if record.get('Driving License') == 'Yes' else False,
                            'joining_date': record.get('Joining Date'),
                            'private_email': record.get('Private Email'),
                            'phone': record.get('Private Phone'),
                            'identification_id': record.get('Identification No'),
                            'passport_id': record.get('Passport No'),
                            'gender': gender,
                            'marital': marital_status,
                            'birthday': record.get('Date of Birth'),
                            'place_of_birth': record.get('Place of Birth'),
                            'study_field': record.get('Field of Study'),
                            'study_school': record.get('School'),
                            'spouse_birthdate': record.get('Spouse Birthdate'),
                            'spouse_complete_name': record.get('Spouse Complete Name'),
                            'visa_no': record.get('Visa No'),
                            'permit_no': record.get('Work Permit No'),
                            'visa_expire': record.get('Visa Expire Date'),
                            'certificate': record.get('Certificate Level')
                        }
                        if record.get('Work In') != '':
                            work_in = self.env['res.partner'].search([('name', '=', record.get('Work In'))], limit=1)
                            if not work_in:
                                work_in = self.env['res.partner'].create({'name': record.get('Work In')})
                            employee_vals.update({'work_in': work_in.id})
                        if record.get('Visa Status') != '':
                            visa_status = self.env['visa.status'].search(
                                [('visa_status', '=', record.get('Visa Status'))],
                                limit=1)
                            if not visa_status:
                                visa_status = self.env['visa.status'].create({'visa_status': record.get('Visa Status')})
                            employee_vals.update({'visa': visa_status.id})
                        if record.get('Department') != '':
                            department_id = self.env['hr.department'].search([('name', '=', record.get('Department'))],
                                                                             limit=1)
                            if not department_id:
                                department_id = self.env['hr.department'].create({'name': record.get('Department')})
                            employee_vals.update({'department_id': department_id.id})
                        if record.get('Job Position') != '':
                            job_id = self.env['hr.job'].search([('name', '=', record.get('Job Position'))], limit=1)
                            if not job_id:
                                job_id = self.env['hr.job'].create({'name': record.get('Job Position')})
                            employee_vals.update({'job_id': job_id.id})
                        if record.get('Manager') != '':
                            parent_id = self.env['hr.employee'].search([('name', 'ilike', record.get('Manager'))],
                                                                       limit=1)
                            if not parent_id:
                                parent_id = self.env['hr.employee'].create({'name': record.get('Manager')})
                            employee_vals.update({'parent_id': parent_id.id})
                        if record.get('Home Leave Destination') != '':
                            home_leave_destination = self.env['res.country'].search(
                                [('name', '=', record.get('Home Leave Destination').split(', ')[1])], limit=1)
                            if not home_leave_destination:
                                home_leave_destination = self.env['res.country'].create(
                                    {'name': record.get('Home Leave Destination').split(', ')[1]})
                            employee_vals.update({'home_leave_destination': home_leave_destination.id})
                        if record.get('Country of Issue') != '':
                            country_issue = self.env['res.country'].search(
                                [('name', '=', record.get('Country of Issue'))], limit=1)
                            if not country_issue:
                                country_issue = self.env['res.country'].create(
                                    {'name': record.get('Country of Issue')})
                            employee_vals.update({'country_issue': country_issue.id})
                        if record.get('Work Address') != '':
                            address_id = self.env['res.partner'].search([('name', '=', record.get('Work Address'))],
                                                                        limit=1)
                            if not address_id:
                                address_id = self.env['res.partner'].create({'name': record.get('Work Address')})
                            employee_vals.update({'address_id': address_id.id})
                        if record.get('Coach') != '':
                            coach_id = self.env['hr.employee'].search([('name', 'ilike', record.get('Coach'))], limit=1)
                            if not coach_id:
                                coach_id = self.env['hr.employee'].create({'name': record.get('Coach')})
                            employee_vals.update({'parent_id': coach_id.id})
                        if record.get('Address') != '':
                            address_home_id = self.env['res.partner'].search([('name', '=', record.get('Address'))],
                                                                             limit=1)
                            if not address_home_id:
                                address_home_id = self.env['res.partner'].create({'name': record.get('Address')})
                            employee_vals.update({'address_home_id': address_home_id.id})
                        if record.get('Address (Home Country)') != '':
                            address_home_country = self.env['res.partner'].search(
                                [('name', '=', record.get('Address (Home Country)'))], limit=1)
                            if not address_home_country:
                                address_home_country = self.env['res.partner'].create(
                                    {'name': record.get('Address (Home Country)')})
                            employee_vals.update({'address_home_country': address_home_country.id})
                        if record.get('Nationality (Country)') != '':
                            country_id = self.env['res.country'].search(
                                [('name', '=', record.get('Nationality (Country)'))], limit=1)
                            if not country_id:
                                country_id = self.env['res.country'].create(
                                    {'name': record.get('Nationality (Country)')})
                            employee_vals.update({'country_id': country_id.id})
                        if record.get('Country of Birth') != '':
                            country_of_birth = self.env['res.country'].search(
                                [('name', '=', record.get('Country of Birth'))], limit=1)
                            if not country_of_birth:
                                country_of_birth = self.env['res.country'].create(
                                    {'name': record.get('Country of Birth')})
                            employee_vals.update({'country_of_birth': country_of_birth.id})
                        if record.get('Certificate Level') == 'Bachelor':
                            employee_vals.update({'certificate': 'bachelor'})
                        elif record.get('Certificate Level') == 'Master':
                            employee_vals.update({'certificate': 'master'})
                        elif record.get('Certificate Level') == 'Other':
                            employee_vals.update({'certificate': 'other'})

                        if record.get('Dependants/Name') != '':
                            dependant_line = False
                            dob = False
                            if record.get('Dependants/Date of Birth') != '':
                                dob = xlrd.xldate_as_datetime(record.get('Dependants/Date of Birth'),
                                                              0).strftime('%Y-%m-%d')
                            if employee:
                                dependant_line = self.env['hr.dependant'].search(
                                    [('name', '=', record.get('Dependants/Name')), ('hr_employee', '=', employee.id)],
                                    limit=1)
                            if dependant_line:
                                dependant_vals = [(1, dependant_line.id, {
                                    'dob': dob,
                                    'relation': record.get('Dependants/Relationship'),
                                    'gender': record.get('Dependants/Sex'),
                                    'accompany': True if record.get(
                                        'Dependants/Are they accompanying you?') == 'Yes' else False,
                                })]
                                employee_vals.update({'dependant_id': dependant_vals})
                            else:
                                dependant_vals = [(0, 0, {
                                    'name': record.get('Dependants/Name'),
                                    'dob': dob,
                                    'relation': record.get('Dependants/Relationship'),
                                    'gender': record.get('Dependants/Sex'),
                                    'accompany': True if record.get(
                                        'Dependants/Are they accompanying you?') == 'Yes' else False,
                                })]
                            employee_vals.update({'dependant_id': dependant_vals})

                        if record.get('Emergency/Name') != '':
                            emergency_line = False
                            if employee:
                                emergency_line = self.env['hr.emergency'].search(
                                    [('name', '=', record.get('Emergency/Name')), ('hr_employee', '=', employee.id)],
                                    limit=1)
                            if emergency_line:
                                emergenecy_vals = [(1, emergency_line.id, {
                                    'relation': record.get('Emergency/Relationship'),
                                    'address': record.get('Emergency/Address'),
                                    'telephone': record.get('Emergency/Telephone No.'),
                                    'mobile': record.get('Emergency/Mobile No.'),
                                    'fax': record.get('Emergency/Fax'),
                                    'location': record.get('Emergency/Location')
                                })]
                                employee_vals.update({'emergency_id': emergenecy_vals})
                            else:
                                emergenecy_vals = [(0, 0, {
                                    'name': record.get('Emergency/Name'),
                                    'relation': record.get('Emergency/Relationship'),
                                    'address': record.get('Emergency/Address'),
                                    'telephone': record.get('Emergency/Telephone No.'),
                                    'mobile': record.get('Emergency/Mobile No.'),
                                    'fax': record.get('Emergency/Fax'),
                                    'location': record.get('Emergency/Location')
                                })]
                            employee_vals.update({'emergency_id': emergenecy_vals})

                        if record.get('School/College/University/Year') != '':
                            education_line = False
                            if employee:
                                education_line = self.env['hr.education'].search(
                                    [('year', '=', record.get('School/College/University/Year')),
                                     ('hr_employee', '=', employee.id)], limit=1)
                            if education_line:
                                education_vals = [(1, education_line.id, {
                                    'degree': record.get('School/College/University/Degree'),
                                    'school_college': record.get('School/College/University/School College'),
                                    'university': record.get('School/College/University/University'),
                                })]
                                employee_vals.update({'education_id': education_vals})
                            else:
                                education_vals = [(0, 0, {
                                    'year': record.get('School/College/University/Year'),
                                    'degree': record.get('School/College/University/Degree'),
                                    'school_college': record.get('School/College/University/School College'),
                                    'university': record.get('School/College/University/University'),
                                })]
                            employee_vals.update({'education_id': education_vals})
                        if record.get('Courses/Course Title') != '':
                            courses_id = False
                            if employee:
                                courses_id = self.env['hr.courses'].search(
                                    [('course_title', '=', record.get('Courses/Course Title')),
                                     ('hr_employee', '=', employee.id)], limit=1)
                            if record.get('Courses/From') != '':
                                from_date = xlrd.xldate_as_datetime(record.get('Courses/From'), 0).strftime('%Y-%m-%d')
                            else:
                                from_date = False
                            if record.get('Courses/To') != '':
                                to_date = xlrd.xldate_as_datetime(record.get('Courses/To'), 0).strftime('%Y-%m-%d')
                            else:
                                to_date = False
                            if courses_id:
                                courses_vals = [(1, courses_id.id, {
                                    'from_date': from_date,
                                    'qualification': record.get('Courses/Qualification'),
                                    'to_date': to_date,
                                    'institution': record.get('Courses/Institution/Address'),
                                })]
                                employee_vals.update({'courses_id': courses_vals})
                            else:
                                courses_vals = [(0, 0, {
                                    'course_title': record.get('Courses/Course Title'),
                                    'from_date': from_date,
                                    'qualification': record.get('Courses/Qualification'),
                                    'to_date': to_date,
                                    'institution': record.get('Courses/Institution/Address'),
                                })]
                            employee_vals.update({'courses_id': courses_vals})

                        if record.get('Language/Name') != '':
                            language_id = False
                            if employee:
                                language_id = self.env['hr.language'].search(
                                    [('name', '=', record.get('Language/Name')), ('hr_employee', '=', employee.id)],
                                    limit=1)
                            if language_id:
                                language_vals = [(1, language_id.id, {
                                    'spoken': record.get('Language/Spoken'),
                                    'oral': record.get('Language/Oral'),
                                    'written': record.get('Language/Written')
                                })]
                                employee_vals.update({'language_id': language_vals})
                            else:
                                language_vals = [(0, 0, {
                                    'name': record.get('Language/Name'),
                                    'spoken': record.get('Language/Spoken'),
                                    'oral': record.get('Language/Oral'),
                                    'written': record.get('Language/Written')
                                })]
                            employee_vals.update({'language_id': language_vals})

                        if record.get('Employment History/Position') != '':
                            history_id = False
                            if employee:
                                history_id = self.env['hr.history'].search(
                                    [('position', '=', record.get('Employment History/Position')),
                                     ('hr_employee', '=', employee.id)], limit=1)
                            if history_id:
                                history_vals = [(1, history_id.id, {
                                    'company_institution': record.get('Employment History/Company/Institution'),
                                    'date': record.get('Employment History/Date')
                                })]
                                employee_vals.update({'history_id': history_vals})
                            else:
                                history_vals = [(0, 0, {
                                    'position': record.get('Employment History/Position'),
                                    'company_institution': record.get('Employment History/Company/Institution'),
                                    'date': record.get('Employment History/Date')
                                })]
                            employee_vals.update({'history_id': history_vals})
                        if employee:
                            employee.write(employee_vals)
                        else:
                            self.create(employee_vals)
            except Exception as e:
                print('Something Wrong', e)

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
            dependants = []
            if res.dependant_id:
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
