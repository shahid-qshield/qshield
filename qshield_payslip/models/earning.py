from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class Earning(models.Model):
    _name = 'qshield.earning'

    # @api.model
    def _get_basic_salary_payable(self):
        _logger.info('in default2')
        _logger.info(self.amount)
        return self.amount

    name = fields.Char(string='Name', required=True)
    amount = fields.Float(string='Amount')
    payable = fields.Float(string='Payable', default=_get_basic_salary_payable)
    payslip_id = fields.Many2one('qshield.payslip')
