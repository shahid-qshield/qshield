from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


def get_years():
    year_list = []
    for i in range(1990, 2036):
        year_list.append((str(i), str(i)))
    _logger.info('testtest')
    _logger.info(year_list)
    return year_list


class Payslip(models.Model):
    _name = 'qshield.payslip'

    @api.model
    def _get_basic_salary_payable(self):
        _logger.info('in default1')
        _logger.info(self.basic_salary_amount)
        return self.basic_salary_amount

    employee_id = fields.Many2one('hr.employee', required=True)
    qid = fields.Char(related='employee_id.identification_id', string='QID')
    designation_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Designation')
    contract_id = fields.Many2one('hr.contract', compute='_get_employee_contract')
    date_of_joining = fields.Date(string='Date of Joining', related='contract_id.date_start')
    currency_id = fields.Many2one('res.currency', string='Currency', related='contract_id.currency_id')
    month = fields.Selection([
            ('1', 'JANUARY'),
            ('2', 'FEBRUARY'),
            ('3', 'MARCH'),
            ('4', 'APRIL'),
            ('5', 'MAY'),
            ('6', 'JUNE'),
            ('7', 'JULY'),
            ('8', 'AUGUST'),
            ('9', 'SEPTEMBER'),
            ('10', 'OCTOBER'),
            ('11', 'NOVEMBER'),
            ('12', 'DECEMBER'),
        ])
    year = fields.Selection(get_years(), string='Year')

    basic_salary_amount = fields.Monetary(related='contract_id.basic_salary', store=True)
    basic_salary_payable = fields.Monetary(default=_get_basic_salary_payable)

    housing_allowance_amount = fields.Monetary(related='contract_id.housing_allowance')
    housing_allowance_payable = fields.Monetary()

    transport_allowance_amount = fields.Monetary(related='contract_id.transport_allowance')
    transport_allowance_payable = fields.Monetary()

    telephone_allowance_amount = fields.Monetary(related='contract_id.telephone_allowance')
    telephone_allowance_payable = fields.Monetary()

    petrol_allowance_amount = fields.Monetary(related='contract_id.petrol_allowance')
    petrol_allowance_payable = fields.Monetary()

    other_allowance_amount = fields.Monetary(related='contract_id.other_allowance')
    other_allowance_payable = fields.Monetary()

    gross_salary = fields.Monetary(string='Gross Salary', compute='_get_gross_salary', readonly=True)

    earning_ids = fields.One2many('qshield.earning', 'payslip_id', string='Earnings')
    deduction_ids = fields.One2many('qshield.deduction', 'payslip_id', string='Deduction')

    total_earning = fields.Monetary(string='Total Earning', compute='_get_total_earning')
    total_deduction = fields.Monetary(string='Total Deduction', compute='_get_total_deduction')

    payment_mode = fields.Char(string='Payment Mode')
    bank_id = fields.Many2one('res.bank', string='Bank')
    account_number = fields.Char(string='Account Number')
    net_pay = fields.Monetary(string='Net Pay', compute='_get_net_pay')
    net_pay_in_words = fields.Char(compute='_get_net_pay_in_words')

    @api.onchange('employee_id')
    def _get_employee_contract(self):
        for record in self:
            if record.employee_id:
                contract = self.env['hr.contract'].search([
                    ('employee_id', '=', record.employee_id.id),
                    ('state', '=', 'open')
                ], limit=1)
                if contract:
                    record.contract_id = contract.id

    @api.onchange('basic_salary_amount', 'housing_allowance_amount', 'transport_allowance_amount',
                  'telephone_allowance_amount', 'petrol_allowance_amount', 'other_allowance_amount')
    @api.depends('basic_salary_amount', 'housing_allowance_amount', 'transport_allowance_amount',
                 'telephone_allowance_amount', 'petrol_allowance_amount', 'other_allowance_amount')
    def _get_gross_salary(self):
        for record in self:
            record.gross_salary = record.basic_salary_amount + record.housing_allowance_amount + record.transport_allowance_amount + record.telephone_allowance_amount + record.petrol_allowance_amount + record.other_allowance_amount

    @api.depends('deduction_ids')
    def _get_total_deduction(self):
        self.total_deduction = 0.0
        for record in self:
            if record.deduction_ids:
                for deduction in record.deduction_ids:
                    record.total_deduction = record.total_deduction + deduction.amount

    @api.depends('earning_ids')
    def _get_total_earning(self):
        self.total_earning = 0.0
        for record in self:
            if record.earning_ids:
                for earning in record.earning_ids:
                    record.total_earning = record.total_earning + earning.amount

    @api.depends('gross_salary', 'total_earning', 'total_deduction')
    def _get_net_pay(self):
        for record in self:
            record.net_pay = (record.gross_salary + record.total_earning) - record.total_deduction

    def _get_net_pay_in_words(self):
        text = ''
        for record in self:
            text = record.currency_id.amount_to_text(record.net_pay) + ' Only'
            record.net_pay_in_words = text

    # @api.model
    # def default_get(self, fields):
    #     _logger.info('in default_get method')
    #     _logger.info(self.contract_id.basic_salary)
    #     res = super(Payslip, self).default_get(fields)
    #     res.update({
    #         'basic_salary_payable': self.basic_salary_amount,
    #     })
    #     return res
