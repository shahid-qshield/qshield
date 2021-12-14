from odoo import models, fields, api
from datetime import datetime, date


# from dateutil.relativedelta import relativedelta


class HRContractCustom(models.Model):
    _inherit = 'hr.contract'

    home_country = fields.Many2one(comodel_name="world.airports", required=False)
    joining_date = fields.Date(string="Joining Date", related="employee_id.joining_date", required=True)
    eligible_for_ticket = fields.Boolean(default=False)
    ticket_period = fields.Selection(default="1", selection=[('half', 'Half Year'), ('1', '1 Year'),
                                                             ('2', '2 Years')], required=False)
    ticket_balance = fields.Integer(default=0, required=False)
    leave_id = fields.One2many('hr.leave', 'hr_contract', index=True,
                               readonly=False, domain="[('employee_id.id', '=', employee_id)]")

    def _update_balance(self):
        contracts = self.search([('state', '=', 'open')])
        for each in contracts:
            each.ticket_balance = 0
            if each.eligible_for_ticket:
                num_years = (date.today().year - each.joining_date.year) + (
                        date.today().month - each.joining_date.month) / 12
                period = 1.0
                if each.ticket_period == 'half':
                    period = 0.5
                elif each.ticket_period == '2':
                    period = 2.0
                total_years = num_years / period
                if total_years >= 1.0:
                    total_ticket_balance = total_years
                    approved_leaves = self.env['hr.leave'].search_count(
                        [('hr_contract', '=', each.id), ('state', '=', 'validate')])
                    if approved_leaves and total_ticket_balance > approved_leaves:
                        each.ticket_balance = total_ticket_balance - approved_leaves
