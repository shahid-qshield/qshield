from dateutil import relativedelta
from odoo import models, fields, api
from datetime import datetime
from odoo.addons.resource.models.resource import HOURS_PER_DAY
from pytz import UTC


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    current_leave_state = fields.Selection(selection_add=[('finance', 'Finance')])


class HRLeaveCustom(models.Model):
    _inherit = 'hr.leave'

    contact_while_away = fields.Char(string="Contact # while away", default="", required=False, )
    actual_departure = fields.Date(string="Actual Departure", default=lambda self: fields.Datetime.now(),
                                   related='request_date_from', required=False, readonly=False)
    # air_ticket = fields.Boolean(string="Air Ticket ?", default=False)
    air_ticket = fields.Selection(string="Air Ticket ?", default="",
                                  selection=[('y', 'Yes'), ('n', 'No')], required=False)
    air_ticket_entitlement = fields.Selection(string="Air Ticket Entitlement", default="",
                                              selection=[('y', 'Yes'), ('n', 'No')], required=False)
    handover_required = fields.Selection(string="Handover Required", default="",
                                         selection=[('y', 'Yes'), ('n', 'No')], required=False)
    employee_outsource = fields.Many2one(string="", related="employee_id.work_in")
    destination_to = fields.Many2one(comodel_name="world.airports", string="Airport Destination", required=False)
    job_assigned_to = fields.Many2one(comodel_name="hr.employee", string="Job Assigned to",
                                      domain="[('work_in','=',employee_outsource), ('id','!=',employee_id)]",
                                      required=False)
    total_days_available = fields.Float(string="", compute="get_total_days")
    # total_days_approved = fields.Float(string="Total Days Approved", default=0)
    approved_date = fields.Date(string="", default=lambda self: fields.Datetime.now())
    loan_date = fields.Date(string="", default=lambda self: fields.Datetime.now())
    initial_requested_days = fields.Float(string="", default=0)
    requested_days_before_approve = fields.Float(string="", default=0)
    terms_of_payments = fields.Integer(string="", default=0, required=False, )
    balance_amount = fields.Float(string="", store=True)
    end_of_service_benefit = fields.Float(store=True)
    state = fields.Selection(selection_add=[('finance', 'Finance')])

    total_number_of_approved_leave_days = fields.Float(string="get_total_days", default=0)
    hr_contract = fields.Many2one('hr.contract', related="employee_id.contract_id")
    is_approved = fields.Boolean(default=False)
    leave_selection = fields.Selection(selection=[
        ('working_days', 'Working Days'),
        ('calendar_days', 'Calendar Days')],
        compute="compute_leave_selection", store=True)

    @api.depends('employee_id')
    def compute_leave_selection(self):
        for leave in self:
            if leave.employee_id and leave.employee_id.contract_id:
                leave.leave_selection = leave.employee_id.contract_id.leave_selection
            else:
                leave.leave_selection = False

    # @api.depends('total_days_approved')
    # @api.onchange('total_days_approved')
    # def change_end_date(self):
    #     if self.total_days_approved != 0:
    #         self.request_date_to = self.request_date_from + relativedelta.relativedelta(
    #             days=self.total_days_approved - 1)
    #         self.date_to = self.request_date_to

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)
            if employee and employee.contract_id and employee.contract_id.leave_selection == 'calendar_days':
                if date_from and date_to:
                    days = (date_to - date_from).days + 1
                    hours = days * 24
                    if employee.contract_id.resource_calendar_id:
                        hours = days * employee.contract_id.resource_calendar_id.hours_per_day
                    elif employee.resource_calendar_id:
                        hours = days * employee.resource_calendar_id.hours_per_day
                    return {'days': days, 'hours': hours}
            else:
                return super(HRLeaveCustom, self)._get_number_of_days(date_from, date_to, employee_id)
        else:
            return super(HRLeaveCustom, self)._get_number_of_days(date_from, date_to, employee_id)

    @api.model
    def create(self, vals):
        if vals.get('number_of_days'):
            vals['initial_requested_days'] = vals.get('number_of_days')
        return super(HRLeaveCustom, self).create(vals)

    # def write(self,vals):
    #     print(self.state)
    #     # self.requested_days_before_approve = self.number_of_days
    #     print(self.number_of_days)
    #     print(self.requested_days_before_approve)

    # return super(HRLeaveCustom, self).write(vals)

    @api.depends('number_of_days')
    def _compute_number_of_hours_display(self):
        for holiday in self:
            calendar = holiday._get_calendar()
            if holiday.date_from and holiday.date_to:
                # Take attendances into account, in case the leave validated
                # Otherwise, this will result into number_of_hours = 0
                # and number_of_hours_display = 0 or (#day * calendar.hours_per_day),
                # which could be wrong if the employee doesn't work the same number
                # hours each day
                if holiday.state == 'validate':
                    if holiday.leave_selection == 'calendar_days':
                        days = (holiday.date_to - holiday.date_from).days + 1
                        number_of_hours = days * 24
                        if holiday.employee_id.contract_id.resource_calendar_id:
                            number_of_hours = days * holiday.employee_id.contract_id.resource_calendar_id.hours_per_day
                        elif holiday.employee_id.resource_calendar_id:
                            number_of_hours = days * holiday.employee_id.resource_calendar_id.hours_per_day
                    else:
                        start_dt = holiday.date_from
                        end_dt = holiday.date_to
                        if not start_dt.tzinfo:
                            start_dt = start_dt.replace(tzinfo=UTC)
                        if not end_dt.tzinfo:
                            end_dt = end_dt.replace(tzinfo=UTC)
                        resource = holiday.employee_id.resource_id
                        intervals = calendar._attendance_intervals_batch(start_dt, end_dt, resource)[resource.id] \
                                    - calendar._leave_intervals_batch(start_dt, end_dt, None)[
                                        False]  # Substract Global Leaves
                        number_of_hours = sum((stop - start).total_seconds() / 3600 for start, stop, dummy in intervals)
                else:
                    number_of_hours = \
                        holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['hours']
                holiday.number_of_hours_display = number_of_hours or (
                        holiday.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY))
            else:
                holiday.number_of_hours_display = 0

    @api.depends('employee_id', 'holiday_status_id')
    @api.onchange('employee_id', 'holiday_status_id')
    def get_total_days(self):
        for record in self:
            total_allocation = 0
            allocations = self.env['hr.leave.allocation'].search([('employee_id', '=', record.employee_id.id),
                                                                  ('holiday_status_id', '=',
                                                                   record.holiday_status_id.id)]).mapped(
                'number_of_days_display')
            for allocation in allocations:
                total_allocation += allocation

            approved_leaves = self.env['hr.leave.report'].search([('employee_id', '=', record.employee_id.id),
                                                                  ('state', '=', 'validate')]).mapped('number_of_days')
            # number_of_leaves = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
            #                                                 ('holiday_status_id', '=',
            #                                                  self.holiday_status_id.id)]).mapped('number_of_days')
            # print(approved_leaves)

            record.total_number_of_approved_leave_days = 0
            record.total_days_available = 0
            for leave in approved_leaves:
                if leave < 0:
                    record.total_number_of_approved_leave_days += leave
            # print(self.total_number_of_approved_leave_days)
            # print(allocation + self.total_number_of_approved_leave_days)
            # print(self.total_days_available)

            loanDate = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
                                                   ('state', '=', 'approve')]).date
            loanInstallmentsNumber = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
                                                                 ('state', '=', 'approve')]).installment
            balanceAmount = self.env['hr.loan'].search([('employee_id', '=', record.employee_id.id),
                                                        ('state', '=', 'approve')]).balance_amount

            record.total_days_available = total_allocation + record.total_number_of_approved_leave_days
            record.loan_date = loanDate
            record.terms_of_payments = loanInstallmentsNumber
            record.balance_amount = balanceAmount
        # print(self.total_days_available)

    def action_validate(self):
        super(HRLeaveCustom, self).action_validate()
        if self.hr_contract.ticket_balance:
            print("here")
            self.is_approved = True
            self.hr_contract.ticket_balance -= 1
        self.approved_date = datetime.today()
        if not self.employee_id.is_out_sourced:
            self.state = 'finance'

    def action_refuse(self):
        super(HRLeaveCustom, self).action_refuse()
        if self.is_approved and self.hr_contract.ticket_balance:
            self.is_approved = False
            self.hr_contract.ticket_balance += 1

    def action_finance_department(self):
        self.state = 'validate'

    # @api.onchange("state")
    # @api.depends("state")
    # def _onchange_state(self):
    #     print(self)
    #     for rec in self:
    #         print(rec.state)
    #         if rec.state == 'validate':
    #             print("valid")


class HRLeaveTypeCustom(models.Model):
    _inherit = 'hr.leave.type'

    type = fields.Selection(string="Type", default="",
                            selection=[('annual', 'Annual Leave'), ('sick', 'Sick Leave'),
                                       ('emergency', 'Emergency Leave'), ('others', 'Others')], required=False)
