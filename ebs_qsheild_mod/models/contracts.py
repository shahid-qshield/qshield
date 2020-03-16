# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Contracts(models.Model):
    _name = 'ebs_mod.contracts'
    _description = "Contracts"

    name = fields.Char(
        string='Name',
        required=True)
    contract_date = fields.Date(
        string='Contract Date',
        required=True)
    start_date = fields.Date(
        string='Start Date',
        required=True)
    end_date = fields.Date(
        string='End Date',
        required=True)

    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=True,
        domain=['|', ('company_type', '=', 'company'), ('company_type', '=', 'person')])

    contact_type = fields.Selection(
        string='Contact Type',
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
        readonly=True,
        compute='_get_contact_type',
        store=True)
    desc = fields.Text(
        string="Description",
        required=False)

    @api.depends('contact_id')
    def _get_contact_type(self):
        if self.contact_id:
            self.contact_type = self.contact_id.person_type
