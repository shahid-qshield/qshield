# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ExpenseTypes(models.Model):
    _name = 'ebs_mod.expense.types'
    _description = "Expense Type"


    _sql_constraints = [
        ('expense_type_name_unique', 'unique (name)',
         'Name must be unique !'),
    ]

    name = fields.Char(
        string='Name',
        required=True)
