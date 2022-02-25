# -*- coding: utf-8 -*-
import time
from collections import defaultdict

import babel

from odoo import models, fields, api, tools, _
from datetime import datetime, timezone, time, timedelta
import time


# class HrPayslipInput(models.Model):
#     _inherit = 'hr.payslip.input'
#
#     loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")


# class HrPayslipCustomForLoan(models.Model):
#     _inherit = 'hr.payslip'
#
#     loan = fields.Float(string="Loan Installment", default=0.0, help="Loan installment" )
#
#     @api.onchange('employee_id')
#     def _get_loan(self):
#         print(self.loan)
#         loans = self.env['hr.loan'].search([]).filtered(lambda l: l.state == 'approve' and l.employee_id == self.employee_id)
#         for loan in loans:
#             self.loan = loans.loan_lines.amount
#             print(self.loan)


# class HrPayslip(models.Model):
#     _inherit = 'hr.payslip'
#
#     @api.onchange('employee_id', 'date_from', 'date_to')
#     def onchange_employee(self):
#         if (not self.employee_id) or (not self.date_from) or (not self.date_to):
#             return
#
#         employee = self.employee_id
#         date_from = self.date_from
#         date_to = self.date_to
#         contract_ids = []
#
#         ttyme = datetime.fromtimestamp(time.mktime(time.strptime(str(date_from), "%Y-%m-%d")))
#         locale = self.env.context.get('lang') or 'en_US'
#         self.name = _('Salary Slip of %s for %s') % (
#         employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale)))
#         self.company_id = employee.company_id
#         if self.contract_id:
#             contract_ids = self.get_contract(employee, date_from, date_to)
#             if not contract_ids:
#                 return
#             self.contract_id = self.env['hr.contract'].browse(contract_ids[0])
#         # if not self.contract_id.structure_type_id.struct_ids.filtered(
#         #         lambda x: x.id == self.env.ref('matco_hr_extended.structure_002').id):
#         #     return
#         # self.struct_id = self.contract_id.structure_type_id.struct_ids.filtered(
#         #     lambda x: x.id == self.env.ref('matco_hr_extended.structure_002').id)
#         #
#         contracts = self.env['hr.contract'].browse(contract_ids)
#         if contracts:
#             input_line_ids = self.get_inputs(contracts, date_from, date_to)
#             input_lines = self.input_line_ids.browse([])
#             for r in input_line_ids:
#                 input_lines += input_lines.new(r)
#             self.input_line_ids = input_lines
#         return
#
#     @api.model
#     def create(self, vals):
#         res = super(HrPayslip, self).create(vals)
#         res.onchange_employee()
#         return res
#
#     @api.model
#     def get_contract(self, employee, date_from, date_to):
#
#         clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
#         clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
#         clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
#         clause_final = [('employee_id', '=', employee.id), ('state', '=', 'open'), '|',
#                         '|'] + clause_1 + clause_2 + clause_3
#         return self.env['hr.contract'].search(clause_final).ids
#
#     @api.model
#     def get_inputs(self, contracts, date_from, date_to):
#
#         res = []
#         # structure_ids = contracts.get_all_structures()
#         # rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
#         rule_ids = self.struct_id.get_all_rules()
#         for input in rule_ids:
#             if input.code == 'LO':
#                 input_type = self.env['hr.payslip.input.type'].search([('code', '=', 'LO')])
#                 loan_ids = self.env['hr.loan'].search(
#                     [('employee_id', '=', self.employee_id.id), ('state', '=', 'approve')])
#                 total_loan_installment = 0
#                 print(loan_ids)
#                 for loan in loan_ids:
#                     amount = sum(
#                         loan.loan_lines.filtered(lambda x: x.date >= self.date_from and x.date <= self.date_to).mapped(
#                             'amount'))
#                     total_loan_installment += amount
#                 print(input_type)
#                 if input_type:
#                     input_data = {
#                         'name': input.name,
#                         # 'code': input.code,
#                         'input_type_id': input_type[0].id,
#                         'amount': total_loan_installment
#                     }
#                     res += [input_data]
#
#             contract_obj = self.env['hr.contract']
#             emp_id = contract_obj.browse(contracts.id).employee_id
#             lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('state', '=', 'approve')])
#             # print("=========================================================",lon_obj)
#             for loan in lon_obj:
#                 # print("==========================,",loan)
#                 for loan_line in loan.loan_lines:
#                     # print("==========================,", loan_line)
#                     if date_from <= loan_line.date <= date_to and not loan_line.paid:
#                         for result in res:
#                             # print("============result================",result)
#                             if result.get('name') == 'Loan':
#                                 result['amount'] = loan_line.amount
#                                 result['loan_line_id'] = loan_line.id
#                                 # print("================",result['amount'])
#                                 # print("================",result['loan_line_id'])
#         return res
#
#     def action_payslip_done(self):
#         for line in self.input_line_ids:
#             # print("========================line==========",line.loan_line_id)
#             if line.loan_line_id:
#                 line.loan_line_id.paid = True
#                 line.loan_line_id.loan_id._compute_loan_amount()
#         return super(HrPayslip, self).action_payslip_done()


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    def get_all_structures(self):
        structures = self.structure_type_id.struct_ids.filtered(
            lambda x: x.id == self.env.ref('matco_hr_extended.structure_002').id)
        if not structures:
            return []
        return list(set(structures.ids))


# class HrPayrollStructure(models.Model):
#     _inherit = 'hr.payroll.structure'
#     _description = 'Salary Structure'

    # def get_all_rules(self):
    #     all_rules = []
    #     for struct in self:
    #         all_rules += struct.rule_ids
    #     return all_rules
