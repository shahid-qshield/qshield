# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    responsible_user = fields.Many2one('res.users')
    company_name = fields.Char(string="Company Name")
    business_nature = fields.Char(string="Business Nature")
    company_size = fields.Integer(string="Company Size")

    @api.model
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        if res.type == 'opportunity':
            res.responsible_user = res.user_id.id
        return res

    def write(self, vals):
        order = self.env['sale.order'].search([('opportunity_id', '=', self.id)], order='id desc', limit=1)
        if order and order.is_agreement == 'is_retainer':
            vals.update({'planned_revenue': order.amount_total * 12})
        else:
            vals.update({'planned_revenue': order.amount_total})
        res = super(CrmLead, self).write(vals)
        return res

    def redirect_lead_opportunity_view(self):
        self.ensure_one()
        if self.user_id:
            self.write({'responsible_user': self.user_id.id})
        res = super(CrmLead, self).redirect_lead_opportunity_view()
        return res

    def _create_lead_partner_data(self, name, is_company, parent_id=False):
        res = super(CrmLead, self)._create_lead_partner_data(name, is_company, parent_id)
        res.update({'person_type': 'company'})
        return res

    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order',
                 'order_ids.company_id')
    def _compute_sale_data(self):
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state in ('draft', 'sent', 'quotation_submit', 'quotation_approved'):
                    quotation_cnt += 1
                if order.state not in ('draft', 'sent', 'cancel', 'quotation_submit', 'quotation_approved'):
                    sale_order_cnt += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id,
                        order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt

    def action_view_sale_quotation(self):
        action = super(CrmLead, self).action_view_sale_quotation()
        if 'domain' in action:
            action.update({'domain': [('opportunity_id', '=', self.id),
                                      ('state', 'in', ['draft', 'quotation_submit', 'quotation_approved', 'sent'])]})
        return action

    def action_view_sale_order(self):
        action = super(CrmLead, self).action_view_sale_order()
        if 'domain' in action:
            action.update({'domain': [('opportunity_id', '=', self.id),
                                      ('state', 'not in',
                                       ('draft', 'sent', 'cancel', 'quotation_submit', 'quotation_approved'))]})
        return action

    # over ride method of create partner base on company name

    def _create_lead_partner(self):
        """ Create a partner from lead data
            :returns res.partner record
        """
        Partner = self.env['res.partner']
        contact_name = self.company_name
        if not contact_name:
            contact_name = Partner._parse_partner_name(self.email_from)[0] if self.email_from else False

        if self.partner_name:
            partner_company = Partner.create(self._create_lead_partner_data(self.partner_name, True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None

        if contact_name:
            return Partner.create(
                self._create_lead_partner_data(contact_name, False, partner_company.id if partner_company else False))

        if partner_company:
            return partner_company
        return Partner.create(self._create_lead_partner_data(self.name, False))


class Lead2OpportunityPartner(models.TransientModel):
    _inherit = 'crm.lead2opportunity.partner'

    custom_action = fields.Selection([
        ('create', 'Create a new customer'),
        ('exist', 'Link to an existing customer'),
    ], 'Customer', default="create")

    @api.model
    def default_get(self, fields):
        result = super(Lead2OpportunityPartner, self).default_get(fields)
        if 'user_id' in result:
            result.update({'user_id': self.env.user.id})
        if 'action' in result:
            result.update({'action': 'create'})
        return result

    def action_apply(self):
        if self.custom_action:
            self.write({'action': self.custom_action})
        result = super(Lead2OpportunityPartner, self).action_apply()
        return result
