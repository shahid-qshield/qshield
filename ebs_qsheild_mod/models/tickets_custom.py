# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TicketsCustom(models.Model):
    _inherit = 'helpdesk.ticket'

    related_company = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        store=True,
        related="partner_id.related_company")

    person_type = fields.Selection(
        string='Person Type',
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
        store=True,
        related="partner_id.person_type"
    )

    service_id = fields.Many2one(
        comodel_name='ebs_mod.service.request',
        string='Service',
        required=False)

    service_type_id = fields.Many2one(
        comodel_name='ebs_mod.service.types',
        string='Service Type',
        required=False)


