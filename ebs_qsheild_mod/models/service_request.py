from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date


class ServiceRequest(models.Model):
    _name = 'ebs_mod.service.request'
    _description = "Service Request"
    _inherit = ['mail.activity.mixin', 'mail.thread.blacklist']
    _order = 'date desc'

    code = fields.Char(
        string='Code',
        required=False)
    name = fields.Char(
        string='Name',
        required=False,
        default='/'
    )
    partner_document_count = fields.Integer(
        string='Contact Uploaded Documents Count',
        required=False, default=0)
    start_date = fields.Datetime(
        string='Start Date',
        required=False, readonly=True)

    end_date = fields.Datetime(
        string='End Date',
        required=False, readonly=True)

    service_type_id = fields.Many2one(
        comodel_name='ebs_mod.service.types',
        string='Service Type',
        required=True, domain=[('id', '=', -1)]
    )

    is_started = fields.Boolean(
        string='Is Started',
        required=False, default=False)

    sla_min = fields.Integer(
        string='SLA - Minimum Days',
        store=True,
        required=False,
        related="service_type_id.sla_min", readonly=True)

    sla_max = fields.Integer(
        string='SLA - Maximum Days',
        store=True,
        required=False,
        related="service_type_id.sla_max", readonly=True
    )
    sla_days = fields.Integer(
        string='SLA - Days',
        required=False,
        readonly=True)
    estimated_end_date = fields.Date(
        string='Estimated End Date',
        required=False)

    @api.depends('estimated_end_date')
    def _get_days_to_finish(self):
        for rec in self:
            if rec.estimated_end_date and rec.status == 'complete':
                rec.days_to_finish = self.get_date_difference(datetime.now().date(), rec.estimated_end_date, 1)
            else:
                rec.days_to_finish = 0

    days_to_finish = fields.Integer(
        string='Days to Finish',
        required=False,
        compute="_get_days_to_finish")

    related_company_ro = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        readonly=True
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=True,
    )

    related_company = fields.Many2one(
        comodel_name='res.partner',
        string='Company',

    )

    date = fields.Date(
        string='Date',
        required=True
    )

    @api.onchange('date')
    def _date_on_change(self):
        if self.date:
            if self.env.company.disable_future_date_service:
                if self.date > date.today():
                    self.date = date.today()

    contract_id = fields.Many2one(
        comodel_name='ebs_mod.contracts',
        string='Contract',
        required=True,
        domain=[('id', '=', -1)]
    )

    partner_type = fields.Selection(
        string='Contact Type',
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
        related="partner_id.person_type"
    )
    phone = fields.Char(
        string='Phone',
        readonly=True,
        required=False,
        related="partner_id.phone")

    mobile = fields.Char(
        string='Mobile',
        required=False,
        readonly=True,
        related="partner_id.mobile")

    is_miscellaneous = fields.Boolean(
        string='Is Miscellaneous',
        required=False,
        readonly=True,
        related="partner_id.is_miscellaneous"
    )
    active = fields.Boolean(
        string='Active', default=True,
        required=False)
    email = fields.Char(
        string='Email',
        required=False,
        readonly=True,
        related="partner_id.email")

    desc = fields.Text(
        string="Description",
        required=False)
    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
                   ('progress', 'In Progress'),
                   ('hold', 'On Hold'),
                   ('complete', 'Completed'),
                   ('cancel', 'Canceled'),
                   ('reject', 'Rejected')],
        required=False,
        default='draft')
    status_dict = {
        'draft': 'Draft',
        'progress': 'In Progress',
        'hold': 'On Hold',
        'complete': 'Completed',
        'reject': 'Rejected',
        'cancel': 'Canceled'
    }
    cost_center = fields.Char(
        string='Cost Center',
        required=False)

    flow_type = fields.Selection(
        string='Workflow Type',
        selection=[('o', 'Online'),
                   ('m', 'Manual'), ],
        required=True)

    service_flow_ids = fields.One2many(
        comodel_name='ebs_mod.service.request.workflow',
        inverse_name='service_request_id',
        string='Workflow',
        required=False)

    service_document_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='service_id',
        string='Documents',
        required=False)

    expenses_ids = fields.One2many(
        comodel_name='ebs_mod.service.request.expenses',
        inverse_name='service_request_id',
        string='Expenses',
        required=False)

    def _compute_service_document_count(self):
        for rec in self:
            rec.document_count = len(self.env['documents.document'].search([('service_id', '=', rec.id)]))

    document_count = fields.Integer(
        string='Document Count',
        required=False,
        compute="_compute_service_document_count")

    status_sla = fields.Selection([('normal', 'Normal'),
                                   ('exceeded', 'Exceeded'), ], default='normal', string=' SLA Status')

    progress_date = fields.Date('Progress Date')
    exceeded_date = fields.Date('Exceeded Date')
    exceeded_days = fields.Integer('Exceeded Days', compute="_compute_exceeded_days", store=-True)

    @api.depends('status', 'status_sla', 'exceeded_date')
    def _compute_exceeded_days(self):
        for rec in self:
            if rec.status == 'progress':
                if rec.status_sla == 'exceeded':
                    if rec.exceeded_date:
                        rec.exceeded_days = rec.exceeded_date.day - rec.progress_date.day

    def compute_exceeded_requests(self):
        recordset = self.search([('status', '=', 'progress'), ('status_sla', '=', 'normal')])
        for record in recordset:
            if record.sla_max:
                max_days = timedelta(days=record.sla_max)
                today = fields.Date.today()
                if record.progress_date:
                    if (today + max_days) > record.progress_date:
                        record.write({'status_sla': 'exceeded'})
                        record.exceeded_date = fields.Date.today()
                        service_group = self.env.ref('ebs_qsheild_mod.group_service_manager')
                        service_users = self.env['res.users'].search([('groups_id', 'in', [service_group.id])])
                        notification_ids = []
                        for user in service_users:
                            notification_ids.append((0, 0, {
                                'res_partner_id': user.partner_id.id,
                                # 'group_public_id': service_group.id,
                                'notification_type': 'inbox'}))
                        channels = self.env['mail.channel'].search(
                            [('id', '=', self.env.ref('ebs_qsheild_mod.channel_service_manager_group').id)])
                        if channels:
                            channels.message_post(
                                body='This Service Request %s has been Exceeded! with %s exceeded days ' % (
                                record.name, record.exceeded_days), message_type='notification',
                                subtype='mail.mt_comment', author_id=self.env.user.partner_id.id,
                                notification_ids=notification_ids)

    @api.model
    def create(self, vals):
        vals['related_company_ro'] = vals['related_company']
        res = super(ServiceRequest, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('related_company', False):
            vals['related_company_ro'] = vals['related_company']
        if vals.get('cost_center', False):
            if self.cost_center:
                if vals['cost_center'] != self.cost_center:
                    self.message_post(
                        body="Cost Center changed from " + self.cost_center + " to " + vals['cost_center'] + ".")
        if vals.get('status', False):
            if vals['status'] != self.status:
                self.message_post(
                    body="Status changed from " + self.status_dict[self.status] + " to " + self.status_dict[
                        vals['status']] + ".")
        res = super(ServiceRequest, self).write(vals)
        return res

    def action_see_documents(self):
        self.ensure_one()
        return {
            'name': _('Documents'),
            'res_model': 'documents.document',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'), (False, 'tree'), (False, 'form')],
            'view_mode': 'kanban',
            'context': {
                "search_default_service_id": self.id,
                "default_service_id": self.id,
                "searchpanel_default_folder_id": False,
                "hide_contact": True,
                "hide_service": True
            },
        }

    @api.onchange('partner_id', 'date')
    def partner_company_onchange(self):
        self.contract_id = None
        self.service_type_id = None
        if self.env.context.get('default_partner_id', False):
            self.partner_id = self.env.context.get('default_partner_id')
        if self.date and self.partner_id:

            if self.partner_id.person_type == 'company':
                self.related_company_ro = self.partner_id.id
                self.related_company = self.partner_id.id
            else:
                self.related_company_ro = self.partner_id.related_company.id
                self.related_company = self.partner_id.related_company.id

            contract_list = self.env['ebs_mod.contracts'].search([
                ('contact_id', '=', self.related_company.id),
                ('start_date', '<=', self.date),
                ('end_date', '>=', self.date),
            ])
            if len(contract_list) == 0:
                return {'warning': {'title': _('Warning'),
                                    'message': _('No contract found for this company and date combination.')}}
            else:
                if self.partner_id.person_type == 'company':
                    return {
                        'domain': {
                            'contract_id': [('contact_id', '=', self.related_company.id),
                                            ('start_date', '<=', self.date),
                                            ('end_date', '>=', self.date), ]
                        }
                    }
                else:
                    contact_contract_list = self.get_contact_contract_list(self.partner_id, contract_list)
                    if len(contact_contract_list) == 0:
                        return {'warning': {'title': _('Warning'),
                                            'message': _(
                                                'Selected contact not found in contracts related contacts')}}
                    else:
                        self.contract_id = contact_contract_list[0]
                        return {
                            'domain': {
                                'contract_id': [('id', 'in', contact_contract_list)]
                            }
                        }

    def get_contact_contract_list(self, contact, contract_list):
        contact_contract_list = []
        for rec in contract_list:
            if self.check_contract_contact(rec, contact):
                contact_contract_list.append(rec.id)
        return contact_contract_list

    @api.onchange('contract_id')
    def contract_id_on_change(self):
        self.service_type_id = None
        if self.contract_id:
            if self.contract_id.service_ids:
                contact_service_list = self.get_contact_related_service_types(self.contract_id.service_ids.ids,
                                                                              self.partner_id)
                return {
                    'domain':
                        {
                            'service_type_id': [('id', 'in', contact_service_list)]
                        }
                }
            else:
                return {'warning': {'title': _('Warning'),
                                    'message': _(
                                        'Selected contract has no services for this contact type')}}

    def get_contact_related_service_types(self, service_type_ids, contact_id):
        domain = [('id', 'in', service_type_ids)]
        if contact_id.person_type == 'emp':
            domain.append(('for_employee', '=', True))
        elif contact_id.person_type == 'visitor':
            domain.append(('for_visitor', '=', True))
        elif contact_id.person_type == 'child':
            domain.append(('for_dependant', '=', True))
        else:
            domain.append(('for_company', '=', True))

        if contact_id.is_miscellaneous:
            domain.append(('for_miscellaneous', '=', True))
        else:
            domain.append(('for_not_miscellaneous', '=', True))

        services_list = self.env['ebs_mod.service.types'].search(domain)
        if len(services_list) == 0:
            return []
        else:
            return services_list.ids

    def check_contract_contact(self, contract, contact_id):
        contact_list = []
        if contact_id.person_type == 'emp':
            contact_list = contract.employee_list.ids
        elif contact_id.person_type == 'visitor':
            contact_list = contract.visitor_list.ids
        elif contact_id.person_type == 'child':
            contact_list = contract.dependant_list.ids
        if contact_id.id in contact_list:
            return True
        else:
            return False

    def request_submit(self):
        if len(self.service_flow_ids) == 0:
            raise ValidationError(_("Missing Workflow!"))

        # if len(self.env['ebs_mod.service.request.workflow'].search(
        #         [('service_request_id', '=', self.id), ('start_count_flow', '=', True)])) != 1:
        #     raise ValidationError(_("Must have 1 workflow with start count checked!"))

        if self.code:
            code = self.code
        else:
            code = self.env['ir.sequence'].next_by_code('ebs_mod.service.request')

        year = str(self.date.year)
        month = self.date.strftime("%B")
        comp_ref = self.related_company.ref or ""
        service_red = self.service_type_id.code or ""
        self.code = code
        self.name = comp_ref + "-" + service_red + "-" + month + year + "-" + code
        self.status = 'progress'
        self.progress_date = fields.Date.today()

        # if self.flow_type == 'o':
        #     flow_list = self.service_type_id.workflow_online_ids
        # else:
        #     flow_list = self.service_type_id.workflow_manual_ids
        #
        # for flow in flow_list:
        #     self.env['ebs_mod.service.request.workflow'].create({
        #         'service_request_id': self.id,
        #         'workflow_id': flow.id,
        #     })

    def get_date_difference(self, start, end, jump):
        delta = timedelta(days=jump)
        start_date = start
        end_date = end
        count = 0
        while start_date < end_date:
            start_date += delta
            count += 1
        return count

    def request_cancel(self):
        for flow in self.service_flow_ids:
            flow.status = 'cancel'
        self.end_date = datetime.today()
        if self.start_date and self.end_date:
            self.sla_days = self.get_date_difference(self.progress_date, self.end_date.date(), 1)
        else:
            self.sla_days = 0
        self.status = 'cancel'

    def request_reject(self):
        for flow in self.service_flow_ids:
            flow.status = 'reject'
        self.end_date = datetime.today()
        if self.progress_date and self.end_date:
            self.sla_days = self.get_date_difference(self.progress_date, self.end_date.date(), 1)
        else:
            self.sla_days = 0
        self.status = 'reject'

    def request_complete(self):
        complete = True
        # for flow in self.service_flow_ids:
        #     if flow.status == 'pending' or flow.status == 'progress' or flow.status == 'hold':
        #         complete = False
        #         break
        if complete:
            self.end_date = datetime.today()
            if self.progress_date:
                self.sla_days = self.get_date_difference(self.progress_date, self.end_date.date(), 1)
            else:
                self.sla_days = 0
            self.status = 'complete'
        else:
            raise ValidationError(_("Workflow still pending or in progress."))

    def request_hold(self):
        self.status = 'hold'

    def request_progress(self):
        self.status = 'progress'

    def request_draft(self):

        if len(self.service_flow_ids) == 0 and len(self.service_document_ids) == 0 and len(self.expenses_ids) == 0:
            self.start_date = None
            self.end_date = None
            self.status = 'draft'
        else:
            raise ValidationError(_("Delete all Related Items."))

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.name))
        return result

    def unlink(self):
        for rec in self:
            if len(rec.service_document_ids) != 0:
                raise ValidationError(_("Delete Related Documents"))
            for flow in rec.service_flow_ids:
                flow.unlink()
        return super(ServiceRequest, self).unlink()


class ServiceRequestExpenses(models.Model):
    _name = "ebs_mod.service.request.expenses"
    _description = "Service Request Expenses"
    _order = 'date'

    expense_type_id = fields.Many2one(
        comodel_name='ebs_mod.expense.types',
        string='Expense type',
        required=True)

    service_request_id = fields.Many2one(
        comodel_name='ebs_mod.service.request',
        string='Service Request',
        required=True)

    related_company_ro = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        related="service_request_id.related_company_ro"
    )
    contract_id = fields.Many2one(
        comodel_name='ebs_mod.contracts',
        string='Contract',
        related="service_request_id.contract_id"
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        related="service_request_id.partner_id"
    )

    partner_type = fields.Selection(
        string='Contact Type',
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
        related="partner_id.person_type"
    )

    desc = fields.Text(
        string="Description",
        required=False)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True)
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
        default=0.0)

    date = fields.Date(
        string='Payment Date',
        required=True)

    payment_by = fields.Char(
        string='Payment By',
        required=True)
