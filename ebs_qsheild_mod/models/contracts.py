# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime
import math


class Contracts(models.Model):
    _name = 'ebs_mod.contracts'
    _description = "Contracts"

    name = fields.Char(
        string='Name',
        required=True)
    start_date = fields.Date(
        string='Start Date',
        required=True)
    end_date = fields.Date(
        string='End Date',
        required=True)

    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Company',
        required=True,
        domain=[('person_type', '=', 'company')])

    contract_type = fields.Selection(
        string='Contract Type',
        selection=[('retainer_agreement', 'Service Agreement Retainer'),
                   ('transaction_agreement', 'Service Agreement per Transaction'),
                   ('tech_agreement', 'Technical Agreement')],
        required=True, )
    payment_term = fields.Selection(
        string='Payment Term',
        selection=[('monthly', 'Monthly'),
                   ('yearly', 'Yearly')],
        required=[('contract_type', '=', 'retainer_agreement')],
        default='monthly')
    payment_amount = fields.Float(
        string='Amount',
        required=[('contract_type', '=', 'retainer_agreement')],
        default=10000.0)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=[('contract_type', '=', 'retainer_agreement')],
        default=159)
    desc = fields.Text(
        string="Description",
        required=False)

    employees = fields.Many2many(comodel_name="res.partner",
                                 relation="ebs_mod_m2m_contract_contact",
                                 column1="contract_id",
                                 column2="contact_id",
                                 string="Employees",
                                 # domain=employees_domain
                                 )

    @api.model
    def create(self, vals):
        start_date = datetime.strptime(vals['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(vals['end_date'], "%Y-%m-%d")
        contract_days = (end_date - start_date).days
        if contract_days < 365:
            raise ValidationError(_("Contract is minimum for 1 year"))
        contract = super(Contracts, self).create(vals)
        emp_id_list = []
        emp_list = self.env['res.partner'].search([('parent_id', '=', self.contact_id.id)])
        for emp in emp_list:
            emp_id_list.append(emp.id)
        contract.write({'employees': [(6, 0, emp_id_list)]})
        return contract

    def write(self, vals):
        if 'start_date' in vals or 'end_date' in vals:
            start_date = None
            end_date = None
            if 'start_date' in vals:
                start_date = datetime.strptime(vals['start_date'], "%Y-%m-%d")
            else:
                start_date = datetime.combine(self.start_date.today(), datetime.min.time())
            if 'end_date' in vals:
                end_date = datetime.strptime(vals['end_date'], "%Y-%m-%d")
            else:
                end_date = datetime.combine(self.end_date.today(), datetime.min.time())
            contract_days = (end_date - start_date).days
            if contract_days < 365:
                raise ValidationError(_("Contract is minimum for 1 year"))
        if 'contact_id' in vals:
            if self.contact_id:
                emp_id_list = []
                emp_list = self.env['res.partner'].search([('parent_id', '=', self.contact_id.id)])
                for emp in emp_list:
                    emp_id_list.append(emp.id)
                vals['employees'] = [(6, 0, emp_id_list)]
            else:
                vals['employees'] = [(6, 0, [])]
        return super(Contracts, self).write(vals)
