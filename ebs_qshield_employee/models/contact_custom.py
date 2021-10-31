# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContactCustom(models.Model):
    _inherit = 'res.partner'

    nearest_land_mark = fields.Char()
    fax_number = fields.Char('Fax No.')
    employee_id = fields.Many2one('hr.employee', string='Related Employee', index=True)
