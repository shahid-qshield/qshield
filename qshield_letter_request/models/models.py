# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class qshield_letter_request(models.Model):
#     _name = 'qshield_letter_request.qshield_letter_request'
#     _description = 'qshield_letter_request.qshield_letter_request'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
