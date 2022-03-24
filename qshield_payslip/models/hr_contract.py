from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrContractInherit(models.Model):
    _inherit = 'hr.contract'

    def unlink(self):
        for record in self:
            payslips = self.env['qshield.payslip'].search_count([('contract_id', '=', record.id)])
            if payslips:
                raise UserError(
                    'You cannot delete a contract has payslips')
        return super(HrContractInherit, self).unlink()
