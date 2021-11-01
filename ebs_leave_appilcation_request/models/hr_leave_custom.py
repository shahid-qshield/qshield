from dateutil import relativedelta
from odoo import models, fields, api
from datetime import date, datetime


class HRLeaveCustom(models.Model):
    _inherit = 'hr.leave'

    contact_while_away = fields.Char(string="Contact # while away", default="", required=False, )
    actual_departure = fields.Date(string="Actual Departure", default=lambda self: fields.Datetime.now(),
                                   required=False)
    # air_ticket = fields.Boolean(string="Air Ticket ?", default=False)
    air_ticket = fields.Selection(string="Air Ticket ?", default="",
                                  selection=[('y', 'Yes'), ('n', 'No')], required=False)
    air_ticket_entitlement = fields.Selection(string="Air Ticket Entitlement", default="",
                                              selection=[('y', 'Yes'), ('n', 'No')], required=False)
    handover_required = fields.Selection(string="Handover Required", default="",
                                         selection=[('y', 'Yes'), ('n', 'No')], required=False)
    employee_outsource = fields.Boolean(string="", related="employee_id.is_out_sourced")
    destination_to = fields.Many2one(comodel_name="world.airports", string="Airport Destination", required=False)
    job_assigned_to = fields.Many2one(comodel_name="hr.employee", string="Job Assigned to",
                                      domain="[('is_out_sourced','=',employee_outsource)]", required=False)
    total_days_available = fields.Float(string="", compute="get_total_days")
    total_days_approved = fields.Float(string="Total Days Approved", default=0)
    approved_date = fields.Date(string="", default=lambda self: fields.Datetime.now())
    loan_date = fields.Date(string="", default=lambda self: fields.Datetime.now())
    terms_of_payments = fields.Integer(string="", default=0, required=False, )
    balance_amount = fields.Float(string="", store=True)
    state = fields.Selection(selection_add=[('finance', 'Finance')])
    total_number_of_approved_leave_days = fields.Float(string="get_total_days", default=0)

    @api.depends('total_days_approved')
    @api.onchange('total_days_approved')
    def change_end_date(self):
        if self.total_days_approved != 0:
            self.request_date_to = self.request_date_from + relativedelta.relativedelta(
                days=self.total_days_approved - 1)
            self.date_to = self.request_date_to

    @api.depends('employee_id', 'holiday_status_id')
    @api.onchange('employee_id', 'holiday_status_id')
    def get_total_days(self):

        allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', self.employee_id.id),
                                                             ('holiday_status_id', '=',
                                                              self.holiday_status_id.id)]).number_of_days_display
        number_of_leaves = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                                        ('holiday_status_id', '=',
                                                         self.holiday_status_id.id)]).mapped('number_of_days')
        for leave in number_of_leaves:
            self.total_number_of_approved_leave_days += leave

        loanDate = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id),
                                               ('state', '=', 'approve')]).date
        loanInstallmentsNumber = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id),
                                                             ('state', '=', 'approve')]).installment
        balanceAmount = self.env['hr.loan'].search([('employee_id', '=', self.employee_id.id),
                                                    ('state', '=', 'approve')]).balance_amount

        self.total_days_available = allocation - self.total_number_of_approved_leave_days
        self.loan_date = loanDate
        self.terms_of_payments = loanInstallmentsNumber
        self.balance_amount = balanceAmount

    def action_validate(self):
        super(HRLeaveCustom, self).action_validate()
        self.approved_date = datetime.today()
        if not self.employee_id.is_out_sourced:
            self.state = 'finance'

    def action_finance_department(self):
        self.state = 'validate'


class HRLeaveTypeCustom(models.Model):
    _inherit = 'hr.leave.type'

    type = fields.Selection(string="Type", default="",
                            selection=[('annual', 'Annual Leave'), ('sick', 'Sick Leave'),
                                       ('emergency', 'Emergency Leave'), ('others', 'Others')], required=False)
