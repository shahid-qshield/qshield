# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContractsCustom(models.Model):
    _inherit = 'hr.contract'

    leave_entitlement = fields.Char('Leave Entitlement')
    basic_salary = fields.Monetary('Basic Salary')
    housing_allowance = fields.Monetary('Housing Allowance')
    transport_allowance = fields.Monetary('Transport Allowance')
    telephone_allowance = fields.Monetary('Telephone Allowance')
    petrol_allowance = fields.Monetary('Petrol Allowance')
    other_allowance = fields.Monetary('Other Allowance')
    other_benefits = fields.Monetary('Other Benefits')
