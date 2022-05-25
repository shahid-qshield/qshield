# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContractsCustom(models.Model):
    _inherit = 'hr.contract'

    leave_entitlement = fields.Char('Leave Entitlement')
    leave_selection = fields.Selection(selection=[
        ('working_days', 'Working Days'),
        ('calendar_days', 'Calendar Days')],
        store=True, default='working_days')
    contract_type = fields.Selection(string='Contract Type',
                                     selection=[
                                         ('limited', 'Limited'),
                                         ('unlimited', 'Unlimited')],
                                     store=True)
    contract_duration = fields.Integer('Contract Duration')
    basic_salary = fields.Monetary('Basic Salary', default=0)
    housing_allowance = fields.Monetary('Housing Allowance', default=0)
    transport_allowance = fields.Monetary('Transport Allowance', default=0)
    telephone_allowance = fields.Monetary('Telephone Allowance', default=0)
    petrol_allowance = fields.Monetary('Petrol Allowance', default=0)
    other_allowance = fields.Monetary('Other Allowance', default=0)
    other_benefits = fields.Monetary('Other Benefits', default=0)
    gross_salary = fields.Monetary('Gross Salary', compute="_compute_gross_salary")

    def _compute_gross_salary(self):
        for record in self:
            record.gross_salary = record.wage + record.housing_allowance + record.transport_allowance + \
                                  record.telephone_allowance + record.petrol_allowance + record.other_allowance + \
                                  record.other_benefits
