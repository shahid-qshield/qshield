# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class qshield_access_right(models.Model):
#     _name = 'qshield_access_right.qshield_access_right'
#     _description = 'qshield_access_right.qshield_access_right'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
