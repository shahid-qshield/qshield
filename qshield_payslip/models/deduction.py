from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError

class Deduction(models.Model):
    _name = 'qshield.deduction'
    name = fields.Char(string='Name', required=True)
    amount = fields.Float(string='Amount')
    payable = fields.Float(string='Payable')
    payslip_id = fields.Many2one('qshield.payslip')