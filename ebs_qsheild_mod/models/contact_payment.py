# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ContactPayment(models.Model):
    _name = 'ebs_mod.contact.payment'
    _description = "contact payment"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=True)
    partner_type = fields.Selection(
        string='Contact Type', store=True,
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
        related="partner_id.person_type"
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True)

    amount = fields.Float(
        string='Amount',
        required=True, default=0.0)

    desc = fields.Text(
        string="Description",
        required=False)
