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

    contact_list = fields.Many2many(comodel_name="res.partner",
                                    relation="ebs_mod_m2m_contract_contact",
                                    column1="contract_id",
                                    column2="contact_id",
                                    string="Contacts",
                                    # domain=employees_domain
                                    )

    dependant_list = fields.Many2many(comodel_name="res.partner",
                                      relation="ebs_mod_m2m_contract_contact",
                                      column1="contract_id",
                                      column2="contact_id",
                                      string="Dependants",
                                      # domain=employees_domain
                                      )

    @api.depends('contact_id')
    def _compute_hide_notebook(self):
        for rec in self:
            if rec.contact_id:
                rec.hide_notebook = False
            else:
                rec.hide_notebook = True

    hide_notebook = fields.Boolean(
        string='Hide Notebook',
        required=False, default=False, compute='_compute_hide_notebook')

    # @api.onchange('contact_id')
    # def contact_id_onchange(self):
    #     if self.contact_id:
    #         return {
    #             'domain':{
    #                 'employee'
    #             }
    #         }

    def add_all_employee(self):
        emp_list = self.env['res.partner'].search([
            ('parent_id', '=', self.contact_id.id),
            ('person_type', '=', 'emp')
        ])
        for emp in emp_list:
            self.write({'contact_list': [(4, emp.id)]})

    def remove_all_employee(self):
        for contact in self.contact_list:
            if contact.person_type == 'emp':
                self.write({'contact_list': [(3, contact.id)]})

    def add_all_visitor(self):
        emp_list = self.env['res.partner'].search([
            ('parent_id', '=', self.contact_id.id),
            ('person_type', '=', 'visitor')
        ])
        for emp in emp_list:
            self.write({'contact_list': [(4, emp.id)]})

    def remove_all_visitor(self):
        for contact in self.contact_list:
            if contact.person_type == 'visitor':
                self.write({'contact_list': [(3, contact.id)]})

    def add_all_dependent(self):
        emp_list = self.env['res.partner'].search([
            ('parent_id', '=', self.contact_id.id),
            ('person_type', '=', 'visitor')
        ])
        for emp in emp_list:
            self.write({'contact_list': [(4, emp.id)]})

    def remove_all_dependent(self):
        for contact in self.contact_list:
            if contact.person_type == 'child':
                self.write({'contact_list': [(3, contact.id)]})

    @api.model
    def create(self, vals):
        start_date = datetime.strptime(vals['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(vals['end_date'], "%Y-%m-%d")
        contract_days = (end_date - start_date).days
        if contract_days < 365:
            raise ValidationError(_("Contract is minimum for 1 year"))
        contract = super(Contracts, self).create(vals)
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
                vals['employees'] = [(6, 0, [])]
        return super(Contracts, self).write(vals)
