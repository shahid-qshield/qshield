# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContractsCustom(models.Model):
    _inherit = 'hr.contract'

    leave_entitlement = fields.Char('Leave Entitlement')
    contract_type = fields.Selection(string='Contract Type',
                                     selection=[
                                         ('limited', 'Limited'),
                                         ('unlimited', 'Unlimited')],
                                     store=True)
    contract_duration = fields.Integer('Contract Duration')
    basic_salary = fields.Monetary('Basic Salary')
    housing_allowance = fields.Monetary('Housing Allowance')
    transport_allowance = fields.Monetary('Transport Allowance')
    telephone_allowance = fields.Monetary('Telephone Allowance')
    petrol_allowance = fields.Monetary('Petrol Allowance')
    other_allowance = fields.Monetary('Other Allowance')
    other_benefits = fields.Monetary('Other Benefits')
