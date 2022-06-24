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

    employee_list = fields.Many2many(comodel_name="res.partner",
                                     relation="ebs_mod_m2m_contract_emp",
                                     column1="contract_id",
                                     column2="contact_id",
                                     string="Employees",
                                     # domain=employees_domain
                                     )

    visitor_list = fields.Many2many(comodel_name="res.partner",
                                    relation="ebs_mod_m2m_contract_visitor",
                                    column1="contract_id",
                                    column2="contact_id",
                                    string="Visitors",
                                    # domain=employees_domain
                                    )
    dependant_list = fields.Many2many(comodel_name="res.partner",
                                      relation="ebs_mod_m2m_contract_dependant",
                                      column1="contract_id",
                                      column2="contact_id",
                                      string="Dependants",
                                      # domain=employees_domain
                                      )

    service_ids = fields.Many2many(
        comodel_name='ebs_mod.service.types',
        relation="ebs_mod_m2m_contract_services_type",
        column1="contract_id",
        column2="service_type_id",
        string='Services')

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

    def add_all_employee(self):
        emp_list = self.env['res.partner'].search([
            ('parent_id', '=', self.contact_id.id),
            ('person_type', '=', 'emp')
        ])
        if len(emp_list) == 0:
            raise ValidationError(_("No Employees Available"))
        for emp in emp_list:
            self.write({'employee_list': [(4, emp.id)]})

    def remove_all_employee(self):
        self.write({'employee_list': [(6, 0, [])]})

    def add_all_visitor(self):
        emp_list = self.env['res.partner'].search([
            ('parent_id', '=', self.contact_id.id),
            ('person_type', '=', 'visitor')
        ])
        if len(emp_list) == 0:
            raise ValidationError(_("No Visitors Available"))
        for emp in emp_list:
            self.write({'visitor_list': [(4, emp.id)]})

    def remove_all_visitor(self):
        self.write({'visitor_list': [(6, 0, [])]})

    def add_all_dependent(self):
        emp_list = self.env['res.partner'].search([
            ('parent_id', '=', self.contact_id.id),
            ('person_type', '=', 'emp')
        ])
        if len(emp_list) == 0:
            raise ValidationError(_("No Employees Available"))
        inserted = 0
        for emp in emp_list:
            dep_list = self.env['res.partner'].search([
                ('parent_id', '=', emp.id),
                ('person_type', '=', 'child')
            ])
            for child in dep_list:
                inserted += 1
                self.write({'dependant_list': [(4, child.id)]})
        if inserted == 0:
            raise ValidationError(_("No Dependants Available"))

    def remove_all_dependent(self):
        self.write({'dependant_list': [(6, 0, [])]})

    def add_all_services(self):
        services_list = self.env['ebs_mod.service.types'].search([])
        if len(services_list) == 0:
            raise ValidationError(_("No Services Available"))
        for rec in services_list:
            self.write({'service_ids': [(4, rec.id)]})

    def remove_all_services(self):
        self.write({'service_ids': [(6, 0, [])]})

    @api.model
    def create(self, vals):
        start_date = datetime.strptime(vals['start_date'], "%Y-%m-%d")
        end_date = datetime.strptime(vals['end_date'], "%Y-%m-%d")
        # contract_days = (end_date - start_date).days
        if end_date < start_date:
            raise ValidationError(_("End date is before start date"))
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
            # contract_days = (end_date - start_date).days
            if end_date < start_date:
                raise ValidationError(_("End date is before start date"))
        if 'contact_id' in vals:
            if len(self.dependant_list) > 0 or len(self.employee_list) > 0 or len(self.visitor_list) > 0:
                raise ValidationError(_("Cannot edit company, delete linked items."))
        return super(Contracts, self).write(vals)

    def unlink(self):
        for rec in self:
            rec.write({'employee_list': [(6, 0, [])]})
            rec.write({'dependant_list': [(6, 0, [])]})
            rec.write({'visitor_list': [(6, 0, [])]})
            return super(Contracts, rec).unlink()
