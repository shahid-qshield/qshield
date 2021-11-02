# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Courses(models.Model):
    _name = 'visa.status'
    _description = "Visa Status"
    _rec_name = 'visa_status'

    visa_status = fields.Char(string="Status", default="", required=False, )





