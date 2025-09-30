# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from datetime import date, datetime

_request_type = [
    ('noc_visa_application', 'Noc Visa Application'),
    ('salary_certificate', 'Salary Certificate'),
    ('bank_salary_certificate', 'Salary Certificate To The Bank'),
    ('liquor_permit', 'QDC - Application For LIQUOR PERMIT'),
    ('termination_letter', 'Termination Letter'),
    ('job_offer_letter', 'Job Offer Letter'),
]
AVAILABLE_PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Medium'),
    ('2', 'High'),
    ('3', 'Very High'),
]


class EBSHRLetterRequest(models.Model):
    _name = 'ebs.hr.letter.request'
    _inherit = ['mail.thread']
    _description = 'Letter Request'

    def _get_default_employee_id(self):
        return self.env.user.employee_id.id or False

    def _get_domain_employee_id(self):
        if self.env.user.has_group('base.group_user') and not self.env.user.has_group('hr.group_hr_user'):
            return [('id', '=', self.env.user.employee_id.id)]
        else:
            return [(1, '=', 1)]

    name = fields.Char('Letter Request No.', default='New')
    subject_from = fields.Char('Subject From', default='')
    bank_name = fields.Char('Bank', default='')
    notice_period = fields.Char('Notice Period', default='')
    address = fields.Char('Address', default='')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True, tracking=True,
                                  default=_get_default_employee_id, domain=_get_domain_employee_id)
    date_from = fields.Date(string='Date From', required=True, default=fields.Datetime.now(), tracking=True)
    date_to = fields.Date(string='Date To', required=True, default=fields.Datetime.now(), tracking=True)
    termination_date = fields.Date(string='Termination Date', tracking=True)
    date = fields.Date(string='Date', required=True, default=fields.Datetime.now(), tracking=True)
    print_date = fields.Date(string='Print Date', tracking=True)
    priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', index=True,
                                default=AVAILABLE_PRIORITIES[0][0],
                                help='The priority of the request, as an integer: 0 means higher priority, 10 means '
                                     'lower priority.')
    type = fields.Selection(_request_type, required=True, string='Type', tracking=True, readonly=True,
                            default="noc_visa_application")
    addressed_to = fields.Char(string='Addressed To', required=True, copy=False, tracking=True)
    signatory_id = fields.Many2one('hr.employee', string='Signatory', required=True,
                                   domain=[('signatory', '=', True)],
                                   tracking=True)
    description = fields.Text(string="Description", copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    gross_salary = fields.Monetary(string='', compute='get_gross_salary_and_allowances', store=True)
    all_allowances = fields.Monetary(string='', compute='get_gross_salary_and_allowances', store=True)

    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection([
        ('draft', 'draft'),
        ('submitted', 'Submitted'),
        ('under_process', 'Under Process'),
        ('print', 'print'),
        ('ready_for_collection', 'Ready for Collection'),
        ('done', 'Done'),
        ('rejected', 'Rejected')], string='Status', readonly=True, default='draft', tracking=True)
    num_word = fields.Char(string="Wage In Words:", compute='_compute_amount_in_word', store=True)
    wage_num_word = fields.Char(string="Amount In Words:", compute='_compute_amount_in_word', store=True)
    allowances_num_word = fields.Char(string="Allowances In Words:", compute='_compute_amount_in_word', store=True)
    end_of_service_benefit = fields.Float(default=0.0, required=False)
    end_of_service_benefit_word = fields.Char(string="Amount In Words:", compute='_compute_amount_in_word', store=True)

    job_title = fields.Char(string="Job Title")
    contract_duration = fields.Integer(string="Contract Duration")
    probation_period = fields.Char(string="Probation Period")
    contract_start_date = fields.Date(string="Contract Start Date")
    employment_status = fields.Char(string="Employment status")
    monthly_basic_salary = fields.Monetary(string="Monthly Basic Salary")
    monthly_housing_allowance = fields.Monetary(string="Monthly Housing allowance")
    monthly_transportation_allowance = fields.Monetary(string="Monthly Transportation Allowance")
    monthly_other_allowance = fields.Monetary(string="Monthly Other allowance")
    monthly_net_salary = fields.Monetary(string="Monthly Net Salary", compute="compute_monthly_net_salary", store=True)
    annual_air_ticket_management = fields.Text(string="Annual Air Ticket Arrangement",
                                               default="One (1) Economy Class Tickets to Home of Record:")
    medical_and_life_insurance = fields.Text(string="Medical & Life Insurance",
                                             default="Provided Locally as per company policy and Qatari Law -")
    vacation_leave = fields.Text(string="Vacation Leave", default="Options: 30 Calendar days per year, plus Government Holidays \
               21 calendar days per year, plus Government Holidays ")
    sick_leave = fields.Text(string="Sick leave", default="Provided Locally as per company policy and Qatari Law")
    end_of_service_benefit_for_job_offer = fields.Text(string="End Of Service Benefit",
                                                       default="As per Qatar Law, 21 days per year of service")

    @api.depends('monthly_basic_salary', 'monthly_housing_allowance', 'monthly_other_allowance',
                 'monthly_transportation_allowance')
    def compute_monthly_net_salary(self):
        for record in self:
            record.monthly_net_salary = record.monthly_basic_salary + record.monthly_housing_allowance + \
                                        record.monthly_other_allowance + record.monthly_transportation_allowance

    # amount in words
    @api.onchange('gross_salary', 'all_allowances', 'wage_num_word', 'end_of_service_benefit')
    @api.depends('gross_salary', 'all_allowances', 'wage_num_word', 'end_of_service_benefit')
    def _compute_amount_in_word(self):
        for rec in self:
            rec.num_word = str(
                rec.currency_id.with_context(lang='en_US').amount_to_text(rec.gross_salary).strip(
                    ' Rial')) + ' Qatari Riyals'
            rec.allowances_num_word = str(
                rec.currency_id.with_context(lang='en_US').amount_to_text(rec.all_allowances).strip(
                    ' Rial')) + ' Qatari Riyals'
            rec.wage_num_word = str(rec.currency_id.with_context(lang='en_US').amount_to_text(
                rec.employee_id.contract_id.wage).strip(' Rial')) + ' Qatari Riyals'
            rec.end_of_service_benefit_word = str(rec.currency_id.with_context(lang='en_US').amount_to_text(
                rec.end_of_service_benefit).strip(' Rial')) + ' Qatari Riyals'

    # @api.onchange('gross_salary', 'employee_id', 'all_allowances')
    # @api.depends('gross_salary', 'employee_id', 'all_allowances')
    # def _compute_amount_in_word(self):
    #     for rec in self:
    #         rec.num_word = str(
    #             rec.currency_id.with_context(lang='en_US').amount_to_text(rec.gross_salary)) + ' Qatari Riyals'
    #         rec.allowances_num_word = str(
    #             rec.currency_id.with_context(lang='en_US').amount_to_text(rec.all_allowances)) + ' Qatari Riyals'
    #         rec.wage_num_word = str(rec.currency_id.with_context(lang='en_US').amount_to_text(
    #             rec.employee_id.contract_id.wage)) + ' Qatari Riyals'

    @api.onchange('employee_id')
    def _onchange_helpdesk_move_domain(self):
        return {'domain': {'signatory_id': [('id', '!=', self.employee_id.id), ('signatory', '=', True)]}}

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'job_offer_letter':
            self.addressed_to = 'test'
            self.signatory_id = self.env.user.employee_id.id

    @api.onchange('employee_id')
    @api.depends('employee_id')
    def get_gross_salary_and_allowances(self):
        self.monthly_basic_salary = self.employee_id.contract_id.wage
        self.monthly_transportation_allowance = self.employee_id.contract_id.transport_allowance
        self.monthly_other_allowance = self.employee_id.contract_id.other_allowance
        self.monthly_housing_allowance = self.employee_id.contract_id.housing_allowance
        self.contract_duration = self.employee_id.contract_id.contract_duration
        self.contract_start_date = self.employee_id.contract_id.date_start
        self.gross_salary = self.employee_id.contract_id.housing_allowance + self.employee_id.contract_id.petrol_allowance + \
                            self.employee_id.contract_id.other_allowance + self.employee_id.contract_id.telephone_allowance + \
                            self.employee_id.contract_id.transport_allowance + self.employee_id.contract_id.wage

        self.all_allowances = self.employee_id.contract_id.housing_allowance + self.employee_id.contract_id.petrol_allowance + \
                              self.employee_id.contract_id.other_allowance + self.employee_id.contract_id.telephone_allowance + \
                              self.employee_id.contract_id.transport_allowance

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_under_process(self):
        self.write({'state': 'under_process'})

    def action_print_state(self):
        self.write({'state': 'print',
                    'print_date': date.today()})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_submit(self):
        self.ensure_one()
        if self.name == _('New'):
            self.name = self.env['ir.sequence'].next_by_code('ebs.hr.letter.request') or _('New')
        self.write({'state': 'submitted'})
        # self._send_email()

    def action_ready_for_collection(self):
        self.ensure_one()
        self.write({'state': 'ready_for_collection'})
        # self._send_email()

    def action_done(self):
        self.ensure_one()
        self.write({'state': 'done'})

    def get_letter_request_link(self):
        menu_id = self.env.ref('qshield_letter_request.menu_ebs_hr_letter_request').id or False
        action_id = self.env.ref('qshield_letter_request.open_view_ebs_hr_letter_request').id or False
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return base_url + '/web#action=' + str(action_id) + '&id=' + str(self.id) + '&menu_id=' + str(
            menu_id) + '&model=' + self._name + '&view_type=form'

    def action_print(self):
        if self.type == 'noc_visa_application':
            return self.env.ref('qshield_letter_request.noc_visa_application').report_action(self)
        elif self.type == 'salary_certificate':
            return self.env.ref('qshield_letter_request.salary_certificate').report_action(self)
        elif self.type == 'bank_salary_certificate':
            return self.env.ref('qshield_letter_request.salary_certificate_to_bank').report_action(self)
        elif self.type == 'liquor_permit':
            return self.env.ref('qshield_letter_request.qdc_linquor_permit').report_action(self)
        elif self.type == 'termination_letter':
            return self.env.ref('qshield_letter_request.termination_letter').report_action(self)
        elif self.type == 'job_offer_letter':
            return self.env.ref('qshield_letter_request.action_job_offer_report').report_action(self)

    @api.constrains('type', 'state')
    def _check_values(self):
        for rec in self:
            if rec.state == 'under_process':
                if rec.type == 'salary_certificate':
                    if not rec.address:
                        raise ValidationError(_("Please, fill the address of the letter receiver"))
                    if not rec.employee_id.name:
                        raise ValidationError(_("Please, fill Employee's name"))
                    if not rec.employee_id.country_id:
                        raise ValidationError(_("Please, fill Employee's Country name"))
                    if not rec.employee_id.passport_id:
                        raise ValidationError(_("Please, fill Employee's Passport Number"))
                    if not rec.employee_id.qid_number:
                        raise ValidationError(_("Please, fill Employee's QID Number"))
                    if not rec.employee_id.job_id:
                        raise ValidationError(_("Please, fill Employee's Job Position"))
                    if not rec.gross_salary:
                        raise ValidationError(_("Please, make sure that the Employee's salary information is filled"))
                    if not rec.signatory_id:
                        raise ValidationError(_("Please, select Signatory"))
                    if not rec.signatory_id.job_id:
                        raise ValidationError(_("Please, fill Signatory job position"))

                elif rec.type == 'termination_letter':
                    if not rec.employee_id.name:
                        raise ValidationError(_("Please, fill Employee's name"))
                    if not rec.termination_date:
                        raise ValidationError(_("Please, fill Termination date"))
                    if not rec.notice_period:
                        raise ValidationError(_("Please, fill Employee's notice period"))
                    if not rec.bank_name:
                        raise ValidationError(_("Please, fill Employee's bank name"))
                    if not rec.signatory_id:
                        raise ValidationError(_("Please, select Signatory"))
                    if not rec.signatory_id.job_id:
                        raise ValidationError(_("Please, fill Signatory job position"))

                elif rec.type == 'noc_visa_application':
                    if not rec.addressed_to:
                        raise ValidationError(_("Please, fill Addressed to"))
                    if not rec.subject_from:
                        raise ValidationError(_("Please, fill Subject from"))
                    if not rec.employee_id.name:
                        raise ValidationError(_("Please, fill Employee's name"))
                    if not rec.employee_id.country_id:
                        raise ValidationError(_("Please, fill Employee's Country name"))
                    if not rec.employee_id.passport_id:
                        raise ValidationError(_("Please, fill Employee's Passport Number"))
                    if not rec.employee_id.qid_number:
                        raise ValidationError(_("Please, fill Employee's QID Number"))
                    if not rec.employee_id.job_id:
                        raise ValidationError(_("Please, fill Employee's Job Position"))
                    if not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    if not rec.date_from:
                        raise ValidationError(_("Please, fill Date from"))
                    if not rec.date_to:
                        raise ValidationError(_("Please, fill Date to"))
                    if not rec.gross_salary:
                        raise ValidationError(_("Please, make sure that the Employee's salary information is filled"))
                    if not rec.signatory_id:
                        raise ValidationError(_("Please, select Signatory"))
                    if not rec.signatory_id.job_id:
                        raise ValidationError(_("Please, fill Signatory job position"))

                elif rec.type == 'liquor_permit':
                    if not rec.employee_id.name:
                        raise ValidationError(_("Please, fill Employee's name"))
                    if not rec.employee_id.country_id:
                        raise ValidationError(_("Please, fill Employee's Country name"))
                    if not rec.employee_id.passport_id:
                        raise ValidationError(_("Please, fill Employee's Passport Number"))
                    if not rec.employee_id.qid_number:
                        raise ValidationError(_("Please, fill Employee's QID Number"))
                    if not rec.employee_id.job_id:
                        raise ValidationError(_("Please, fill Employee's Job Position"))
                    if not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    if not rec.employee_id.contract_id.wage:
                        raise ValidationError(_("Please, make sure that the Employee's Wage is filled"))
                    if not rec.gross_salary:
                        raise ValidationError(_("Please, make sure that the Employee's salary information is filled"))
                    if not rec.all_allowances:
                        raise ValidationError(_("Please, Check the Employee's Allowances"))
                    if not rec.signatory_id:
                        raise ValidationError(_("Please, select Signatory"))
                    if not rec.signatory_id.job_id:
                        raise ValidationError(_("Please, fill Signatory job position"))

                elif rec.type == 'bank_salary_certificate':
                    if not rec.addressed_to:
                        raise ValidationError(_("Please, fill Addressed to"))
                    if not rec.employee_id.name:
                        raise ValidationError(_("Please, fill Employee's name"))
                    if not rec.employee_id.qid_number:
                        raise ValidationError(_("Please, fill Employee's QID Number"))
                    if not rec.employee_id.job_id:
                        raise ValidationError(_("Please, fill Employee's Job Position"))
                    if not rec.employee_id.joining_date:
                        raise ValidationError(_("Please, fill Employee's Joining date"))
                    if not rec.subject_from:
                        raise ValidationError(_("Please, fill Subject from"))
                    if not rec.gross_salary:
                        raise ValidationError(_("Please, make sure that the Employee's salary information is filled"))
                    if not rec.signatory_id:
                        raise ValidationError(_("Please, select Signatory"))
                    if not rec.signatory_id.job_id:
                        raise ValidationError(_("Please, fill Signatory job position"))

    #             if rec.type == 'salary_breakdown':
    #                 if not rec.employee_id.qid_doc_number:
    #                     raise ValidationError(_("Please, fill Employee's National ID"))
    #                 elif not rec.employee_id.passport_doc_number:
    #                     raise ValidationError(_("Please, fill Employee's Passport number"))
    #                 elif not rec.employee_id.joining_date:
    #                     raise ValidationError(_("Please, fill Employee's Joining date"))
    #                 elif not rec.employee_id.job_title:
    #                     raise ValidationError(_("Please, fill Employee's Job Title"))
    #
    #             if rec.type == 'open_bank_account':
    #                 if not rec.employee_id.qid_doc_number:
    #                     raise ValidationError(_("Please, fill Employee's National ID"))
    #                 elif not rec.employee_id.contract_id.gross_salary:
    #                     raise ValidationError(_("Please, fill Employee's Gross Salary"))
    #                 elif not rec.employee_id.joining_date:
    #                     raise ValidationError(_("Please, fill Employee's Joining date"))
    #                 elif not rec.employee_id.job_title:
    #                     raise ValidationError(_("Please, fill Employee's Job Title"))
    #
    #             if rec.type == 'salary_certificate':
    #                 if not rec.employee_id.country_id.name:
    #                     raise ValidationError(_("Please, fill Employee's Country name"))
    #                 elif not rec.employee_id.id:
    #                     raise ValidationError(_("Please, fill Employee's ID Number"))
    #                 elif not rec.employee_id.joining_date:
    #                     raise ValidationError(_("Please, fill Employee's Joining date"))
    #                 elif not rec.employee_id.qid_doc_number:
    #                     raise ValidationError(_("Please, fill Employee's National ID"))
    #                 elif not rec.employee_id.contract_id.gross_salary:
    #                     raise ValidationError(_("Please, fill Employee's Gross Salary"))
    #
    #             if rec.type == 'salary_transfer_letter':
    #                 if not rec.employee_id.country_id:
    #                     raise ValidationError(_("Please, fill Employee's Country name"))
    #                 elif not rec.employee_id.id:
    #                     raise ValidationError(_("Please, fill Employee's ID Number"))
    #                 elif not rec.employee_id.joining_date:
    #                     raise ValidationError(_("Please, fill Employee's Joining date"))
    #                 elif not rec.employee_id.qid_doc_number:
    #                     raise ValidationError(_("Please, fill Employee's National ID"))
    #                 elif not rec.employee_id.contract_id.gross_salary:
    #                     raise ValidationError(_("Please, fill Employee's Gross Salary"))
    #                 elif not rec.employee_id.contract_id.wage:
    #                     raise ValidationError(_("Please, fill Employee's Salary"))
    #                 elif not rec.employee_id.contract_id.site_allowance:
    #                     raise ValidationError(_("Please, fill Employee's Site Allowance"))
    #                 elif not rec.employee_id.contract_id.transport_allowance:
    #                     raise ValidationError(_("Please, fill Employee's Transportation Allowance"))
    #                 elif not rec.employee_id.contract_id.mobile_allowance:
    #                     raise ValidationError(_("Please, fill Employee's Mobile Allowance"))
    #                 elif not rec.employee_id.contract_id.gross_salary:
    #                     raise ValidationError(_("Please, fill Employee's Gross Salary"))
    #                 elif not rec.employee_id.contract_id.accommodation:
    #                     raise ValidationError(_("Please, fill Employee's Accommodation"))
    #                 elif not rec.employee_id.bank_account_id.acc_number:
    #                     raise ValidationError(_("Please, fill Employee's Bank Account Number"))

    #
    # def _send_email(self):
    #     if self.state == 'submitted':
    #         template_id = self.env.ref('ebs_capstone_hr.submitted_letter_request_email_template').id
    #     elif self.state == 'ready_for_collection':
    #         template_id = self.env.ref('ebs_capstone_hr.ready_for_collection_letter_request_email_template').id
    #     else:
    #         template_id = False
    #     template = self.env['mail.template'].browse(template_id)
    #     template.send_mail(self.id, force_send=True)
    #
    # def action_print(self):
    #     doc = None
    #     name = ""
    #     if self.type == 'letter_to_embassy':
    #         name = 'Letter To Embassy.docx'
    #         doc = self.letter_to_embassy()
    #
    #     elif self.type == 'salary_breakdown':
    #         name = 'Salary Breakdown.docx'
    #         doc = self.salary_breakdown()
    #
    #     elif self.type == 'open_bank_account':
    #         name = 'Salary certificate open bank account.docx'
    #         doc = self.open_bank_account()
    #
    #     elif self.type == 'salary_certificate':
    #         name = 'Salary Certificate.docx'
    #         doc = self.employment_and_salary_certificate()
    #
    #     elif self.type == 'salary_transfer_letter':
    #         name = 'Salary Transfer Letter.docx'
    #         doc = self.salary_transfer_letter()
    #     doc.save(name)
    #
    #     binary_doc = open(name, 'rb')
    #     doc_data = base64.b64encode(binary_doc.read())
    #     record = self.env['ebs.hr.letters.model'].create({
    #         'name': name,
    #         'datas': doc_data
    #     })
    #
    #     binary_doc.close()
    #     os.remove(name)
    #     action = {
    #         'type': "ir.actions.act_url",
    #         'target': "_blank",
    #         'url': '/documents/content/download/%s' % record.id
    #     }
    #
    #     return action
    #
    # def letter_to_embassy(self):
    #     employee = self.employee_id
    #     document = Document()
    #     title = ''
    #     he_she = ''
    #     his_her = ''
    #     if employee.gender == "male":
    #         title = 'Mr'
    #         he_she = 'He'
    #         his_her = 'his'
    #     else:
    #         title = 'Ms'
    #         he_she = 'She'
    #         his_her = 'her'
    #
    #     contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
    #
    #     document.add_paragraph('Date: ' + str(self.date.strftime('%d-%m-%Y')))
    #
    #     font_styles = document.styles
    #     font_styles = font_styles.add_style('Arial12', WD_STYLE_TYPE.PARAGRAPH)
    #     font_object = font_styles.font
    #     font_object.size = Pt(12)
    #     font_object.name = 'Arial'
    #     document.add_paragraph("To: {}\nDoha, Qatar".format(self.addressed_to), style='Arial12')
    #     p2 = document.add_paragraph(style='Arial12')
    #     run = p2.add_run("Attn: Visa section")
    #     run.bold = True
    #     run.underline = True
    #     document.add_paragraph(
    #         "Dear Sir,\nThis is to certify that {} {}, holder of Qatar ID number #{} and {} passport number #{} is a bonafide "
    #         "employee with Bro Technologies. {} is working with us as {} since {} and drawing a monthly gross salary "
    #         "of QR {}\nThis letter is being issued at the specific request of {} {} for visa purpose. Please note that Bro "
    #         "Technologies will not be liable for any liabilities whatsoever arising from out of any transactions made "
    #         "by {} {}\n{} {}, will bear all expenses connected to {} visit.".format(
    #             title, employee.name or "", employee.ikama or "",
    #                    employee.country_id and employee.country_id.name or "",
    #                    employee.passport_id or "", he_she,
    #                    employee.job_id.name and employee.job_id.name or "",
    #             str(employee.joining_date.strftime('%d-%m-%Y')),
    #                    contract and str(contract.gross_salary) or "", title, employee.name, title, employee.name,
    #             title, employee.name, his_her),
    #         style='Arial12')
    #     p6 = document.add_paragraph("Yours truly, \n", style='Arial12')
    #     p6.add_run("For Bro Technologies LLC").bold = True
    #     p7 = document.add_paragraph("_______________________", style='Arial12')
    #     p7.add_run("\n{}\n{}".format(self.signatory_id.name, self.signatory_id.job_title)).bold = True
    #     return document
    #
    # def employment_and_salary_certificate(self):
    #     employee = self.employee_id
    #     document = Document()
    #     title = ''
    #     he_she = ''
    #     his_her = ''
    #     if employee.gender == "male":
    #         title = 'Mr'
    #         he_she = 'He'
    #         his_her = 'his'
    #     else:
    #         title = 'Ms'
    #         he_she = 'She'
    #         his_her = 'her'
    #     contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
    #
    #     font_styles = document.styles
    #     font_styles = font_styles.add_style('Arial12', WD_STYLE_TYPE.PARAGRAPH)
    #     font_object = font_styles.font
    #     font_object.size = Pt(12)
    #     font_object.name = 'Arial'
    #     p1 = document.add_paragraph("Date: {}\nThe Manager".format(str(self.date.strftime('%d-%m-%Y'))),
    #                                 style='Arial12')
    #     p1.add_run('\n{}'.format(self.addressed_to)).bold = True
    #     p1.add_run('\nDoha, Qatar')
    #     p2 = document.add_paragraph(style='Arial12')
    #     p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    #     run = p2.add_run("Subject: Salary certificate")
    #     run.bold = True
    #     run.underline = True
    #     document.add_paragraph(
    #         "This is to certify that {} {}, holder of Qatar ID number #{} and {} passport number #{} is employed "
    #         "with us as {}. {} joined our organization on {} {} present Gross salary is QR {} per month.".format(
    #             title, employee.name, employee.ikama or "", employee.country_id and employee.country_id.name or "",
    #                                   employee.passport_id or "", employee.job_id.name or "", he_she,
    #             str(employee.joining_date.strftime('%d-%m-%Y')), his_her,
    #                                   contract and str(contract.gross_salary) or ""), style='Arial12')
    #     document.add_paragraph(
    #         "This letter is being issued at the specific request of {} {} without any financial obligation to the company.".format(
    #             title, employee.name), style='Arial12')
    #     document.add_paragraph(
    #         "If you need further information regarding {} employment, please contact the undersigned.".format(
    #             his_her),
    #         style='Arial12')
    #     p3 = document.add_paragraph("Yours truly,", style='Arial12')
    #     p3.add_run("\nFor Bro Technologies LLC").bold = True
    #     p4 = document.add_paragraph("_______________________", style='Arial12')
    #     p4.add_run('\n{}'.format(self.signatory_id.name)).bold = True
    #     p4.add_run('\n{}'.format(self.signatory_id.job_title)).bold = True
    #     return document
    #
    # def open_bank_account(self):
    #     employee = self.employee_id
    #     document = Document()
    #     title = ''
    #     he_she = ''
    #     his_her = ''
    #     his_her_small = ''
    #     if employee.gender == "male":
    #         title = 'Mr'
    #         he_she = 'He'
    #         his_her = 'His'
    #         his_her_small = 'his'
    #     else:
    #         title = 'Ms'
    #         he_she = 'She'
    #         his_her = 'Her'
    #         his_her_small = 'her'
    #     contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
    #
    #     font_styles = document.styles
    #     font_styles = font_styles.add_style('Arial12', WD_STYLE_TYPE.PARAGRAPH)
    #     font_object = font_styles.font
    #     font_object.size = Pt(12)
    #     font_object.name = 'Arial'
    #     p1 = document.add_paragraph("Date: {}\nThe Manager".format(str(self.date.strftime('%d-%m-%Y'))),
    #                                 style='Arial12')
    #     p1.add_run('\n{}'.format(self.addressed_to)).bold = True
    #     p1.add_run('\nDoha, Qatar\n\n')
    #     p2 = document.add_paragraph(style='Arial12')
    #     p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    #     run = p2.add_run('Subject: Salary certificate\n\n')
    #     run.bold = True
    #     run.underline = True
    #     document.add_paragraph(
    #         "This is to certify that {} {}, holder of Qatar ID number #{} and {} passport number #{} is employed "
    #         "with us as {}. {} joined our organization on {}. {} present Gross salary is QR {} per "
    #         "month.\n\n".format(
    #             title, employee.name, employee.ikama or '', employee.country_id and employee.country_id.name or "",
    #                                   employee.passport_id or '', employee.job_id.name or '', he_she,
    #             str(employee.joining_date.strftime('%d-%m-%Y')), his_her,
    #                                   contract and str(contract.gross_salary) or ""), style='Arial12')
    #     document.add_paragraph(
    #         "This letter is being issued at the specific request of {} {} for opening a bank account with your bank "
    #         "without any financial obligation to the company.\n\n"
    #         "If you need further information regarding {} employment, please contact the undersigned.\n\n".format(
    #             title, employee.name, his_her_small), style='Arial12')
    #     p7 = document.add_paragraph("Yours truly,", style='Arial12')
    #     p7.add_run("\nFor Bro Technologies LLC\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n  ").bold = True
    #     p9 = document.add_paragraph("_______________________", style='Arial12')
    #     p9.add_run('\n{}\n{}'.format(self.signatory_id.name, self.signatory_id.job_title)).bold = True
    #     return document
    #
    # def salary_transfer_letter(self):
    #     employee = self.employee_id
    #     document = Document()
    #     title = ''
    #     he_she = ''
    #     his_her = ''
    #     him_her = ''
    #     if employee.gender == "male":
    #         title = 'Mr'
    #         he_she = 'He'
    #         his_her = 'his'
    #         him_her = 'him'
    #     else:
    #         title = 'Ms'
    #         he_she = 'She'
    #         his_her = 'her'
    #         him_her = 'her'
    #
    #     contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
    #
    #     font_styles = document.styles
    #     font_styles = font_styles.add_style('Arial12', WD_STYLE_TYPE.PARAGRAPH)
    #     font_object = font_styles.font
    #     font_object.size = Pt(12)
    #     font_object.name = 'Arial'
    #     p1 = document.add_paragraph("Date: {}\nThe Manager".format(str(self.date.strftime('%d-%m-%Y'))),
    #                                 style='Arial12')
    #     p1.add_run('\n{}'.format(self.addressed_to)).bold = True
    #     p1.add_run('\nDoha, Qatar')
    #     p2 = document.add_paragraph(style='Arial12')
    #     p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    #     run = p2.add_run("Subject: Salary Transfer")
    #     run.bold = True
    #     run.underline = True
    #     document.add_paragraph(
    #         "This is to certify that {} {}, holder of Qatar ID number #{} and {} passport number #{} is employed "
    #         "with us as {}. {} joined our organization on {} {} salary breakdown is as following:".format(
    #             title, employee.name, employee.ikama or '', employee.country_id and employee.country_id.name or "",
    #                                   employee.passport_id or '', employee.job_id.name or '', he_she,
    #             str(employee.joining_date.strftime('%d-%m-%Y')), his_her), style='Arial12')
    #     font_styles_table = document.styles
    #     font_styles_table = font_styles_table.add_style('TArial12', WD_STYLE_TYPE.TABLE)
    #     font_styles_table = font_styles_table.font
    #     font_styles_table.size = Pt(12)
    #     font_styles_table.name = 'Arial'
    #     data = (
    #         ('BASIC', contract and str(contract.wage) or ""),
    #         ('Housing Allowance', contract and str(contract.accommodation) or ""),
    #         ('Transportation Allowance', contract and str(contract.transport_allowance) or ""),
    #         ('Mobile Allowance', 'Sim Card and phone Bill are covered by the company'),
    #         ('Total', contract and str(contract.gross_salary) or "")
    #     )
    #     table = document.add_table(1, 2, style='TArial12')
    #     row = table.rows[0]
    #     cell = row.cells[0]
    #     cell2 = row.cells[1]
    #     cell.text = "Name"
    #     cell2.text = "Amount"
    #     run = cell.paragraphs[0].runs[0]
    #     run2 = cell2.paragraphs[0].runs[0]
    #     run.font.bold = True
    #     run2.font.bold = True
    #     for name, amount in data:
    #         row = table.add_row().cells
    #         row[0].text = name
    #         row[1].text = str(amount)
    #     document.add_paragraph(
    #         "To assist {} {} in obtaining a Loan/Credit Card from your bank, we undertake to transfer the monthly "
    #         "salary to {} bank account number {} opening with your bank.".format(
    #             title, employee.name, his_her, employee.bank_account_nb),
    #         style='Arial12')
    #     document.add_paragraph(
    #         "If {} {} resigns or {} employment is terminated by this Company, we undertake to pay all amounts of "
    #         "End of Service Benefit due to {}, after deduction of  any amount due to the company, to {} "
    #         "Bank account with official communication to that respect.".format(
    #             title, employee.name, his_her, him_her, his_her), style='Arial12')
    #     p7 = document.add_paragraph(
    #         "The above-named employee fully understands that Bro Technologies  does not in any way hold itself "
    #         "responsible for any debits incurred by {} and that the granting of loan "
    #         "is the sole discretion of your Bank.\n"
    #         "This letter is being issued at the specific request of {} {} without any financial obligation to the company.\nIf you need further information regarding {} employment, please contact the undersigned.".format(
    #             him_her, title, employee.name, his_her),
    #         style='Arial12')
    #     p10 = document.add_paragraph("Yours truly,", style='Arial12')
    #     p10.add_run("\nFor Bro Technologies LLC").bold = True
    #     p12 = document.add_paragraph("_______________________", style='Arial12')
    #     p12.add_run('\n{}\n{}'.format(self.signatory_id.name, self.signatory_id.job_title)).bold = True
    #     return document
    #
    # def salary_breakdown(self):
    #     employee = self.employee_id
    #     document = Document()
    #     # header = document.sections[0].header
    #     # htable = header.add_table(1, 2, Inches(6))
    #     # htab_cells = htable.rows[0].cells
    #     # ht0 = htab_cells[0].add_paragraph()
    #     # kh = ht0.add_run()
    #     # kh.add_picture('ebs_capstone_hr/static/src/img/Header.png')
    #     # title = ''
    #     # he_she = ''
    #     # his_her = ''
    #     if employee.gender == "male":
    #         title = 'Mr'
    #         he_she = 'He'
    #         his_her = 'his'
    #     else:
    #         title = 'Ms'
    #         he_she = 'She'
    #         his_her = 'her'
    #
    #     contract = self.env['hr.contract'].search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
    #
    #     font_styles = document.styles
    #     font_styles = font_styles.add_style('Arial12', WD_STYLE_TYPE.PARAGRAPH)
    #     font_object = font_styles.font
    #     font_object.size = Pt(12)
    #     font_object.name = 'Arial'
    #     p1 = document.add_paragraph("Date: {}\nThe Manager\n".format(str(self.date.strftime('%d-%m-%Y'))),
    #                                 style='Arial12')
    #     p1.add_run(self.addressed_to).bold = True
    #     p1.add_run("\nDoha, Qatar")
    #     p2 = document.add_paragraph(style='Arial12')
    #     p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    #     p2.add_run("Salary Certificate").bold = True
    #     document.add_paragraph(
    #         "This is to certify that {} {}, holder of Qatar ID number #{} and {} passport number #{} is employed "
    #         "with us as {}. {} joined our organization on {} {} salary breakdown is as following:".format(
    #             title, employee.name, employee.ikama or '', employee.country_id and employee.country_id.name or "",
    #                                   employee.passport_id or '', employee.job_id.name or '', he_she,
    #             str(employee.joining_date.strftime('%d-%m-%Y')), his_her), style='Arial12')
    #     font_styles_table = document.styles
    #     font_styles_table = font_styles_table.add_style('TArial12', WD_STYLE_TYPE.TABLE)
    #     font_styles_table = font_styles_table.font
    #     font_styles_table.size = Pt(12)
    #     font_styles_table.name = 'Arial'
    #     data = (
    #         ('BASIC', contract and str(contract.wage) or ""),
    #         ('Housing Allowance', contract and str(contract.accommodation) or ""),
    #         ('Transportation Allowance', contract and str(contract.transport_allowance) or ""),
    #         ('Mobile Allowance', 'Sim Card and phone Bill are covered by the company'),
    #         ('Total', contract and str(contract.gross_salary) or "")
    #     )
    #     table = document.add_table(1, 2, style='TArial12')
    #     row = table.rows[0]
    #     cell = row.cells[0]
    #     cell2 = row.cells[1]
    #     cell.text = "Name"
    #     cell2.text = "Amount"
    #     run = cell.paragraphs[0].runs[0]
    #     run2 = cell2.paragraphs[0].runs[0]
    #     run.font.bold = True
    #     run2.font.bold = True
    #     for name, amount in data:
    #         row = table.add_row().cells
    #         row[0].text = name
    #         row[1].text = str(amount)
    #     p5 = document.add_paragraph(
    #         "This letter is being issued at the specific request of {} {} without any financial obligation to the "
    #         "company.\nIf you need further information regarding {} employment, please contact the undersigned.\n\n"
    #         "Yours truly,".format(
    #             title, employee.name, his_her), style='Arial12')
    #     p5.add_run("For Bro Technologies LLC").bold = True
    #     p12 = document.add_paragraph("_______________________", style='Arial12')
    #     p12.add_run('\n{}\n{}'.format(self.signatory_id.name, self.signatory_id.job_title)).bold = True
    #     return document
