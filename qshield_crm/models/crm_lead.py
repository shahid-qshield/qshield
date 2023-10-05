# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    responsible_user = fields.Many2one('res.users')
    company_name = fields.Char(string="Company Name")
    business_nature = fields.Char(string="Business Nature")
    company_size = fields.Integer(string="Company Size")
    partner_invoice_type = fields.Selection(
        [('retainer', 'Retainer'), ('per_transaction', 'Per Transaction'),
         ('one_time_transaction', 'One time Transaction'),
         ('partners', 'Partners'), ('outsourcing', 'Outsourcing')])
    parent_company_id = fields.Many2one('res.partner', string="Related Parent Company")
    service_request_ids = fields.One2many('ebs_mod.service.request', 'opportunity_id', string="Services")
    service_request_count = fields.Integer(string="Service count", compute="compute_service_request_count")
    is_readonly_parent_company = fields.Boolean(string="IS Readonly Parent Company",
                                                compute="compute_is_readonly_parent_company")

    @api.depends('partner_id')
    def compute_is_readonly_parent_company(self):
        for record in self:
            record.is_readonly_parent_company = False
            if record.partner_id and record.partner_id.parent_company_id:
                record.is_readonly_parent_company = True

    @api.onchange('partner_invoice_type')
    def onchange_partner_invoice_type(self):
        if self.partner_id and self.partner_id.partner_invoice_type:
            self.partner_invoice_type = self.partner_id.partner_invoice_type

    # @api.onchange('parent_company_id')
    # def onchange_parent_company_id(self):
    #     if self.partner_id and self.partner_id.parent_company_id:
    #         self.parent_company_id = self.partner_id.parent_company_id.id

    @api.depends('service_request_ids')
    def compute_service_request_count(self):
        for record in self:
            if record.service_request_ids:
                record.service_request_count = len(record.service_request_ids)
            else:
                record.service_request_count = 0

    def action_view_service_request(self):
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'ebs_mod.service.request',
            'target': 'current',
            'domain': [('id', 'in', self.service_request_ids.ids if self.service_request_ids else [])],

        }
        return action

    def action_service_request_new(self):
        print('-------------------------------------')
        if self.partner_id:
            context = {
                'search_default_partner_id': self.partner_id.id,
                'default_partner_id': self.partner_id.id,
                'default_opportunity_id': self.id,
                'default_is_one_time_transaction': True
            }
            if self.user_id:
                context.update({'default_activity_user_id': self.user_id.id})
            action = {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'ebs_mod.service.request',
                'target': 'current',
                'context': context,

            }
            return action
        else:
            return True

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id and self.partner_id.parent_company_id:
            self.parent_company_id = self.partner_id.parent_company_id
        elif self.parent_company_id:
            self.parent_company_id = False
        if self.partner_id and self.partner_id.partner_invoice_type:
            self.partner_invoice_type = self.partner_id.partner_invoice_type
        elif self.partner_id and self.partner_invoice_type:
            pass
        elif not self._context.get('from_convert_to_opportunity'):
            self.partner_invoice_type = False
        domain = [('person_type', '=', 'company'), ('parent_company_id', '=', False)]
        if self.partner_invoice_type:
            domain.append(('partner_invoice_type', '=', self.partner_invoice_type))
        if self.partner_id:
            domain.append(('id', '!=', self.partner_id.id))
        return {'domain': {
            'parent_company_id': domain}}

    @api.model
    def create(self, vals):
        res = super(CrmLead, self).create(vals)
        for record in res:
            if record.partner_id and record.partner_id.company_type == 'company':
                record.company_name = record.partner_id.name
            if record.type == 'opportunity':
                record.responsible_user = record.user_id.id
            if record.partner_id and not record.partner_id.partner_invoice_type and record.partner_invoice_type:
                record.partner_id.sudo().write({'partner_invoice_type': record.partner_invoice_type})
            if record.partner_id and not record.partner_id.parent_company_id and record.parent_company_id:
                record.partner_id.sudo().write({'parent_company_id': record.parent_company_id.id})
                message = 'Related Company is set from ' + record.name + " lead" + " and set by " + self.env.user.name
                record.partner_id.message_post(body=message)
        return res

    # def write(self, vals):
    #     order = self.env['sale.order'].search([('opportunity_id', '=', self.id)], order='id desc', limit=1)
    #     if order and order.is_agreement == 'is_retainer':
    #         vals.update({'planned_revenue': order.amount_total * 12})
    #     else:
    #         vals.update({'planned_revenue': order.amount_total})
    #     res = super(CrmLead, self).write(vals)
    #     if vals.get('partner_id'):
    #         partner = self.env['res.partner'].sudo().browse(vals.get('partner_id'))
    #         self.company_name = partner.name
    #     return res

    def write(self, vals):
        for record in self:
            if vals.get('partner_id'):
                partner = self.env['res.partner'].sudo().browse(vals.get('partner_id'))
                if partner:
                    vals.update({'company_name': partner.name})
                if partner and partner.partner_invoice_type:
                    vals.update({'partner_invoice_type': partner.partner_invoice_type})
                if partner and partner.parent_company_id:
                    vals.update({'parent_company_id': partner.parent_company_id.id})
                # if partner and record.partner_invoice_type:
                #     partner.sudo().write({'partner_invoice_type': record.partner_invoice_type})
            # if vals.get('partner_invoice_type'):
            #     record.partner_id.sudo().write({'partner_invoice_type': vals.get('partner_invoice_type')})
            order = self.env['sale.order'].search([('opportunity_id', '=', record.id)], order='id desc', limit=1)
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
            partner_company = Partner.with_context(partner_invoice_type=self.partner_invoice_type,
                                                   parent_company_id=self.parent_company_id).create(
                self._create_lead_partner_data(self.partner_name, True))
        elif self.partner_id:
            partner_company = self.partner_id
        else:
            partner_company = None

        if contact_name:
            return Partner.with_context(partner_invoice_type=self.partner_invoice_type,
                                        parent_company_id=self.parent_company_id).create(
                self._create_lead_partner_data(contact_name, False, partner_company.id if partner_company else False))

        if partner_company:
            return partner_company
        return Partner.with_context(partner_invoice_type=self.partner_invoice_type,
                                    parent_company_id=self.parent_company_id).create(
            self._create_lead_partner_data(self.name, False))


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
        if self.partner_id and self._context.get('active_id') and self._context.get('active_model'):
            lead = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            if lead and self.partner_id.partner_invoice_type:
                lead.write({'partner_invoice_type': self.partner_id.partner_invoice_type})
            if lead and lead.partner_invoice_type and not self.partner_id.partner_invoice_type:
                self.partner_id.write({'partner_invoice_type': lead.partner_invoice_type})
            if lead and self.partner_id.parent_company_id:
                lead.write({'parent_company_id': self.partner_id.parent_company_id.id})
            if lead and lead.parent_company_id and not self.partner_id.parent_company_id:
                self.partner_id.write({'parent_company_id': lead.parent_company_id.id})
        result = super(Lead2OpportunityPartner, self).action_apply()
        return result
