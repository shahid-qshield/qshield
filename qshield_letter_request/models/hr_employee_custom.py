from odoo import models, fields, api


class EmployeeBaseCustom(models.AbstractModel):
    _inherit = 'hr.employee.base'

    signatory = fields.Boolean(string='Signatory')
    letter_ids = fields.One2many('ebs.hr.letter.request', 'employee_id', string='Letter Requests', readonly=True)
    letter_count = fields.Integer(compute='_compute_letter_count', string='Letters Count',
                                  groups="base.group_user")

    def _compute_letter_count(self):
        for employee in self:
            employee.letter_count = len(employee.letter_ids)
