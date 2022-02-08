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
