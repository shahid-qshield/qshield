# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ExcludedCompany(models.Model):
    _name = 'excluded.company'

    related_companies = fields.Many2many('res.partner')

