# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    nearest_land_mark = fields.Char()
    fax_number = fields.Char('Fax No.')
    employee_id = fields.Many2one('hr.employee', string='Related Employee', index=True)

    def create_employee(self):
        for rec in self:
            if not rec.employee_id:
                dependants = []
                for each_dependant in rec.employee_dependants:
                    dependants.append((0, 0, {
                        'name': each_dependant.name,
                        'gender': each_dependant.gender,
                        'dob': each_dependant.date,
                    }))
                employee = self.env['hr.employee'].create({
                    'name': rec.name,
                    'country_id': rec.nationality.id,
                    'gender': rec.gender,
                    'birthday': rec.date,
                    'job_id': rec.function,
                    'work_phone': rec.phone,
                    'mobile_phone': rec.mobile,
                    'work_email': rec.email,
                    'dependant_id': dependants,
                    'partner_id': rec.id,
                })
                # rec.employee_id = employee
