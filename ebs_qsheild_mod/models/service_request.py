from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import re
import logging

logger = logging.getLogger(__name__)


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
        default='/',
        copy=False
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
        required=True)
    for_renewing = fields.Boolean(
        related='service_type_id.for_renewing',
        string='Renewing',
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

    account_manager = fields.Many2one(
        comodel_name='hr.employee',
        string='Account Manager',
        related='related_company_ro.account_manager'
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
                if self.date < date.today():
                    self.date = date.today()

    contract_id = fields.Many2one(
        comodel_name='ebs_mod.contracts',
        string='Contract'
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
        selection=[('draft', 'In Draft'),
                   ('new', 'New'),
                   ('hold', 'On Hold'),
                   ('pending', 'Pending from Gov'),
                   ('progress', 'In Progress'),
                   ('pending_payment', 'Pending Payment'),
                   ('escalated', 'Escalated'),
                   ('reject', 'Rejected'),
                   ('complete', 'Completed'),
                   ('incomplete', 'Incomplete'),
                   ('escalated_progress', 'Escalated In Progress'),
                   ('escalated_incomplete', 'Escalated Incomplete'),
                   ('escalated_complete', 'Escalated Completed'),
                   ('cancel', 'Cancelled by client')],
        required=False,
        default='draft')
    status_dict = {
        'draft': 'Draft',
        'new': 'New',
        'progress': 'In Progress',
        'hold': 'On Hold',
        'pending': 'Pending from Gov',
        'pending_payment': 'Pending Payment',
        'escalated': 'Escalated',
        'incomplete': 'Incomplete',
        'escalated_incomplete': 'Escalated Incomplete',
        'escalated_progress': 'Escalated In Progress',
        'escalated_complete': 'Escalated Completed',
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
    task_count = fields.Integer(string="Task count", compute="compute_task_count")

    service_flow_ids = fields.One2many(
        comodel_name='ebs_mod.service.request.workflow',
        inverse_name='service_request_id',
        string='Workflow',
        required=False,
        copy=True)

    service_document_ids = fields.One2many(
        comodel_name='documents.document',
        inverse_name='service_id',
        string='Documents',
        required=False,
        copy=False)

    expenses_ids = fields.One2many(
        comodel_name='ebs_mod.service.request.expenses',
        inverse_name='service_request_id',
        string='Expenses',
        required=False,
        copy=True)

    def _compute_service_document_count(self):
        for rec in self:
            rec.document_count = len(self.env['documents.document'].search([('service_id', '=', rec.id)]))

    document_count = fields.Integer(
        string='Document Count',
        required=False,
        compute="_compute_service_document_count")

    status_sla = fields.Selection([('normal', 'Normal'),
                                   ('exceeded', 'Exceeded'), ], default='normal', string=' SLA Status')

    progress_date = fields.Date('Start Progress Date')
    completed_date = fields.Date('completed Date')
    exceeded_date = fields.Date('Exceeded Date')
    exceeded_days = fields.Integer('Exceeded Days', compute="_compute_exceeded_days", store=True)
    sla_min_max = fields.Char('SLA Timeline', compute='_concatenate_min_max')
    draft_date = fields.Date('Draft Date')
    new_date = fields.Date('New Date')
    onhold_date = fields.Date('Onhold date')
    pending_from_gov_date = fields.Date('Pending from gov date')
    in_progress_date = fields.Date('In progress Date')
    pending_payment_date = fields.Date('pending payment Date')
    escalated_date = fields.Date('Escalated Date')
    rejected_date = fields.Date('Rejected Date')
    incomplete_date = fields.Date('Incomplete date')
    escalated_in_progress_date = fields.Date('Escalated in progress date')
    escalated_incomplete_date = fields.Date('Escalated incomplete date')
    escalated_complete_date = fields.Date('Escalated complete date')
    cancel_date = fields.Date('cancel date')

    service_document_id = fields.Many2one(
        comodel_name='documents.document',
        string='Documents',
        required=False)

    is_show_status = fields.Boolean('Is Show status', compute='change_status_by_group')
    is_show_new_status = fields.Boolean('Is Show status', compute='change_status_by_group')
    is_edit_status = fields.Boolean('Is Show status', compute='change_status_by_group')
    is_edit_status_new = fields.Boolean('Is Show status', compute='change_status_by_group')

    @api.depends('status')
    def change_status_by_group(self):
        for rec in self:
            # is_show_status = False
            # is_show_new_status = False
            # is_edit_status = False
            # is_edit_status_new = False
            # if self.env.user.has_group(
            #         'ebs_qsheild_mod.qshield_operational_manager'):
            #     is_show_status = True
            #     is_show_new_status = False
            #     is_edit_status = True
            #     is_edit_status_new = False
            # elif self.env.user.has_group('ebs_qsheild_mod.qshield_account_manager'):
            if rec.status in ['draft', 'new']:
                is_show_status = False
                is_show_new_status = True
                is_edit_status = False
                is_edit_status_new = True
            elif self.env.user.has_group('ebs_qsheild_mod.qshield_operational_manager'):
                is_show_status = True
                is_show_new_status = False
                is_edit_status = True
                is_edit_status_new = False
            else:
                is_show_status = True
                is_show_new_status = False
                is_edit_status = False
                is_edit_status_new = False
            rec.is_show_status = is_show_status
            rec.is_show_new_status = is_show_new_status
            rec.is_edit_status = is_edit_status
            rec.is_edit_status_new = is_edit_status_new

    @api.depends('service_flow_ids')
    def compute_task_count(self):
        for record in self:
            if record.service_flow_ids:
                record.task_count = len(record.service_flow_ids)
            else:
                record.task_count = 0

    def update_document_from_cron(self):
        'Author : bhavesh parmar (update res_id and res_model in document)'
        documents = self.env['documents.document'].search([('service_id', '!=', False)])
        for document in documents:
            document.write({'res_id': document.service_id.id,
                            'res_model': document.service_id._name})

    def action_update_end_date(self):
        for rec in self:
            messages = self.env['mail.message'].search([('res_id', '=', rec.id)])
            for message in messages:
                msg = re.search(r'(?<=>).*(?=<)', message.body)
                if msg and msg.group(0) == "Status changed from In Progress to Completed.":
                    service = self.env[message.model].browse(message.res_id)
                    if not service.end_date:
                        service.sudo().write({'end_date': message.date.date()})
                        continue
                incomplete_msg = re.search("^.*to Incomplete.$", msg.group() if msg else '')
                if incomplete_msg:
                    service = self.env[message.model].browse(message.res_id)
                    if not service.end_date:
                        service.sudo().write({'end_date': message.date.date()})
                        continue
                rejected_msg = re.search("^.*to Rejected.$", msg.group() if msg else '')
                if rejected_msg:
                    service = self.env[message.model].browse(message.res_id)
                    if not service.end_date:
                        service.sudo().write({'end_date': message.date.date()})
                        continue
                cancel_msg = re.search("^.*to Canceled.$", msg.group() if msg else '')
                if cancel_msg:
                    service = self.env[message.model].browse(message.res_id)
                    if not service.end_date:
                        service.sudo().write({'end_date': message.date.date()})
                        continue
                escalated_complete_msg = re.search("^.*Escalated Completed.$", msg.group() if msg else '')
                if escalated_complete_msg:
                    service = self.env[message.model].browse(message.res_id)
                    if not service.end_date:
                        service.sudo().write({'end_date': message.date.date()})
                        continue
                escalated_in_complete_msg = re.search("^.*Escalated Incomplete.$", msg.group() if msg else '')
                if escalated_in_complete_msg:
                    service = self.env[message.model].browse(message.res_id)
                    if not service.end_date:
                        service.sudo().write({'end_date': message.date.date()})
                        continue

    @api.onchange('service_type_id', )
    def get_domain_document_id(self):
        for record in self:
            return {'domain': {
                'service_document_id': [('partner_id', '=', record.partner_id.id), ('status', '!=', 'expired')]}}

    def notify_completed_requests(self):
        group_companies = self.read_group(
            domain=[('related_company_ro.account_manager', '!=', False)],
            fields=[],
            groupby=['related_company_ro'])
        for company in group_companies:
            service_requests = self.search([('status', '=', 'complete'), ('end_date', '=', fields.Date.today()),
                                            ('related_company_ro', '=', company['related_company_ro'][0]), ])
            if service_requests:
                items = []
                account_manager = None
                for service in service_requests:
                    account_manager = service.related_company_ro.account_manager
                    items.append(
                        {
                            'Request_Service_Number': service.name,
                            'Request_Service_Type': service.service_type_id.name,
                            'Contact_Name': service.partner_id.name,
                            'Contact_Type': service.partner_type,
                        }
                    )
                body = ''
                if items:
                    for req in items:
                        contact_type_list = [('company', 'Company'),
                                             ('emp', 'Employee'),
                                             ('visitor', 'Visitor'),
                                             ('child', 'Dependent')]
                        contact_type_list = dict(contact_type_list)
                        body += str(req['Contact_Name'])
                        body += ' / '
                        body += contact_type_list[str(req['Contact_Type'])]
                        body += ' / '
                        body += str(req['Request_Service_Type'])
                        body += ' / '
                        body += str(req['Request_Service_Number'])
                        body += '.'
                        body += '<br/>'
                mail = self.env['mail.mail'].sudo().create({
                    'subject': _('Completed Service Requests.'),
                    'email_from': self.env.user.partner_id.email,
                    'author_id': self.env.user.partner_id.id,
                    'email_to': account_manager.user_id.email,
                    'body_html': " Dear {}, <br/> ".format(account_manager.name) + '<br/>' +
                                 "These are the completed service requests with full details <br/>" + '<br/>' +
                                 body
                    ,
                })
                mail.send()

    @api.depends('status', 'status_sla', 'exceeded_date')
    def _compute_exceeded_days(self):
        for rec in self:
            if rec.status == 'progress':
                if rec.status_sla == 'exceeded':
                    if rec.exceeded_date:
                        progress = datetime.strptime(str(rec.progress_date), '%Y-%m-%d')
                        exceeded = datetime.strptime(str(rec.exceeded_date), '%Y-%m-%d')
                        rec.exceeded_days = (exceeded - progress).days
                        # rec.exceeded_days = rec.exceeded_date.day - rec.progress_date.day

    def _concatenate_min_max(self):
        for rec in self:
            name = ""
            # if rec.sla_min:
            name += str(rec.sla_min) + ' ' + 'to' + ' '
            # if rec.sla_max:
            name += str(rec.sla_max)
            rec.sla_min_max = name

    def compute_exceeded_requests(self):
        recordset = self.search([('status', '=', 'progress'), ('status_sla', '=', 'normal')])
        for record in recordset:
            sla_max = 1 if record.sla_max == 0 else record.sla_max
            max_days = timedelta(days=sla_max)
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
        for rec in res:
            rec.draft_date = date.today()
            if rec.service_type_id.for_renewing:
                if rec.service_document_id:
                    rec.service_document_id.renewed = True
        return res

    def write(self, vals):
        is_account_manager_only = False
        if self.env.user.has_group('ebs_qsheild_mod.qshield_account_manager') and not self.env.user.has_group(
                'ebs_qsheild_mod.qshield_operational_manager') and not self._context.get('call_from_dashboard'):
            is_account_manager_only = True
        if self.status not in ['draft', 'new'] and is_account_manager_only and not vals.get(
                'message_main_attachment_id'):
            raise UserError('Account manager group user not allowed write this service')
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
        for rec in self:
            if rec.service_type_id.for_renewing:
                if rec.service_document_id:
                    rec.service_document_id.renewed = True
        res = super(ServiceRequest, self).write(vals)
        is_send_service_notification = self.env['ir.config_parameter'].sudo().get_param(
            'ebs_qsheild_mod.is_send_service_notification')
        if vals.get('status') == 'complete' and self.status == 'complete' and is_send_service_notification:
            self.send_notification_all_account_manager()
        elif vals.get('status') == 'reject' and self.status == 'reject' and is_send_service_notification:
            self.send_notification_all_account_manager()
        elif vals.get('status') == 'cancel' and self.status == 'cancel' and is_send_service_notification:
            self.send_notification_all_account_manager()
        elif vals.get(
                'status') == 'pending_payment' and self.status == 'pending_payment' and is_send_service_notification:
            self.send_notification_all_account_manager()
        elif vals.get(
                'status') == 'incomplete' and self.status == 'incomplete' and is_send_service_notification:
            self.send_notification_all_account_manager()
        elif vals.get(
                'status') == 'escalated_incomplete' and self.status == 'escalated_incomplete' and is_send_service_notification:
            self.send_notification_all_account_manager()
        elif vals.get(
                'status') == 'escalated_complete' and self.status == 'escalated_complete' and is_send_service_notification:
            self.send_notification_all_account_manager()
        return res

    def send_notification_all_account_manager(self):
        template = self.env.ref('ebs_qsheild_mod.mail_template_of_notify_complete_service',
                                raise_if_not_found=False)
        user_sudo = self.env.user
        email_to_list = []
        email_list = []
        service_status = dict(self._fields['status'].selection).get(self.status)
        is_send_service_notification = self.env['ir.config_parameter'].sudo().get_param(
            'ebs_qsheild_mod.is_send_service_notification')
        if is_send_service_notification:
            email_to_list = self.env['ir.config_parameter'].sudo().get_param(
                'ebs_qsheild_mod.send_notification_email')
            email_list = email_to_list.split(',')
            notification_users = self.env['res.users'].sudo().search([('email', 'in', email_list)])
            mail_activity_type = self.env.ref('ebs_qsheild_mod.notification_of_service_status').id
            self.with_context(status=service_status).create_schedule_activity(mail_activity_type, notification_users)
        if template:
            outgoing_server = self.env['ir.mail_server'].sudo().search([('smtp_user', '!=', False)], limit=1)
            if not outgoing_server:
                logger.info("Please configure out going mail server")
            if not email_to_list:
                logger.info("Please configure recipient email in service settings")
            for email_to in email_list:
                complete_date = datetime.now().strftime('%Y-%m-%d %H:%M')
                template.sudo().with_context(username=user_sudo.name, complete_date=complete_date,
                                             email=email_to,
                                             service_status=service_status,
                                             email_from=outgoing_server.smtp_user).send_mail(self.id,
                                                                                             force_send=True)

    def create_schedule_activity(self, mail_activity_type=False, notification_users=False):
        if mail_activity_type and notification_users:
            domain = [
                ('activity_type_id', '=', mail_activity_type),
                ('user_id', 'in', notification_users.ids)
            ]
            if self.env.context.get('workflow'):
                domain.append(('res_model', '=', 'ebs_mod.service.request.workflow'))
                domain.append(('res_id', 'in', self.env.context.get('workflow')))
            else:
                domain.append(('res_model', '=', 'ebs_mod.service.request'))
                domain.append(('res_id', 'in', self.ids))
            activities = self.env['mail.activity'].sudo().search(domain)
            if activities:
                activities.sudo().action_feedback()
            status = self.env.context.get('status') if self.env.context.get('status') else ""
            for user in notification_users:
                if self.env.context.get('workflow'):
                    note = _('Service request workflow status is %s') % status
                    workflow = self.env['ebs_mod.service.request.workflow'].browse(self.env.context.get('workflow'))
                    workflow.activity_schedule(
                        'ebs_qsheild_mod.notification_of_service_workflow_status',
                        note=note,
                        user_id=user.id)
                else:
                    note = _('Service request status is %s') % status
                    self.activity_schedule(
                        'ebs_qsheild_mod.notification_of_service_status',
                        note=note,
                        user_id=user.id)

    def copy(self, default={}):
        default.update({'status': 'draft'})
        default.update({'date': date.today()})
        res = super(ServiceRequest, self).copy(default=default)
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
                if self.partner_id.parent_company_id:
                    self.related_company_ro = self.partner_id.parent_company_id.id
                    self.related_company = self.partner_id.parent_company_id.id
                else:
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
            if len(contract_list) == 0 and self.partner_id.partner_invoice_type in ['retainer', 'outsourcing']:
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
                    if len(contact_contract_list) == 0 and self.partner_id.partner_invoice_type in ['retainer',
                                                                                                    'outsourcing']:
                        return {'warning': {'title': _('Warning'),
                                            'message': _(
                                                'Selected contact not found in contracts related contacts')}}
                    elif contact_contract_list:
                        if self.partner_id.partner_invoice_type in ['retainer',
                                                                 'outsourcing']:
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

    # @api.onchange('contract_id')
    # def contract_id_on_change(self):
    #     self.service_type_id = None
    #     if self.contract_id:
    #         if self.contract_id.service_ids:
    #             contact_service_list = self.get_contact_related_service_types(self.contract_id.service_ids.ids,
    #                                                                           self.partner_id)
    #             return {
    #                 'domain':
    #                     {
    #                         'service_type_id': [('id', 'in', contact_service_list)]
    #                     }
    #             }
    #         else:
    #             return {'warning': {'title': _('Warning'),
    #                                 'message': _(
    #                                     'Selected contract has no services for this contact type')}}

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

    def get_date_difference(self, start, end, jump):
        delta = timedelta(days=jump)
        start_date = start
        end_date = end
        count = 0
        while start_date < end_date:
            start_date += delta
            count += 1
        return count

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

        self.progress_date = fields.Date.today()
        self.new_date = fields.Date.today()

        workflow_id = self.env['ebs_mod.service.request.workflow'].search(
            [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
        if workflow_id:
            if self.progress_date and workflow_id.complete_data:
                self.sla_days = self.get_date_difference(self.progress_date, workflow_id.complete_data, 1)
        else:
            self.sla_days = 0
        self.status = 'new'

    # def request_new(self):
    #     self.status = 'new'

    def request_cancel(self):
        self.end_date = date.today()
        workflow_id = self.env['ebs_mod.service.request.workflow'].search(
            [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
        if workflow_id:
            complete_date = workflow_id.complete_data
            if self.end_date and complete_date:
                self.sla_days = self.get_date_difference(self.end_date.date(), complete_date, 1)
        else:
            self.sla_days = 0
        # self.end_date = datetime.today()
        # if self.start_date and self.end_date:
        #     self.sla_days = self.get_date_difference(self.progress_date, self.end_date.date(), 1)
        # else:
        #     self.sla_days = 0
        self.cancel_date = date.today()
        self.status = 'cancel'
        for flow in self.service_flow_ids:
            flow.status = 'cancel'

    def request_reject(self):
        if self.env.user.has_group('ebs_qsheild_mod.qshield_account_manager') and not self.env.user.has_group(
                'ebs_qsheild_mod.qshield_operational_manager'):
            raise UserError('Account manager groups are not allowed to reject service')
        else:
            self.end_date = date.today()
            workflow_id = self.env['ebs_mod.service.request.workflow'].search(
                [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
            if workflow_id:
                complete_date = workflow_id.complete_data
                if self.end_date and complete_date:
                    self.sla_days = self.get_date_difference(self.end_date.date(), complete_date, 1)
            else:
                self.sla_days = 0
        # self.end_date = datetime.today()
        # if self.progress_date and self.end_date:
        #     self.sla_days = self.get_date_difference(self.progress_date, self.end_date.date(), 1)
        # else:
        #     self.sla_days = 0
        self.rejected_date = date.today()
        self.status = 'reject'
        for flow in self.service_flow_ids:
            flow.status = 'reject'

    def request_complete(self):
        self.completed_date = fields.Date.today()
        self.end_date = fields.Date.today()
        complete = True
        # for flow in self.service_flow_ids:
        #     if flow.status == 'pending' or flow.status == 'progress' or flow.status == 'hold':
        #         complete = False
        #         break
        if complete:
            workflow_id = self.env['ebs_mod.service.request.workflow'].search(
                [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
            if workflow_id:
                complete_date = workflow_id.complete_data
                if self.end_date and complete_date:
                    self.sla_days = self.get_date_difference(self.end_date.date(), complete_date, 1)
            else:
                self.sla_days = 0
            self.status = 'complete'
        else:
            raise ValidationError(_("Workflow still pending or in progress."))

    def request_hold(self):
        self.onhold_date = date.today()
        self.status = 'hold'

    def request_pending(self):
        self.pending_from_gov_date = date.today()
        self.status = 'pending'

    def request_escalated(self):
        self.escalated_date = date.today()
        self.status = 'escalated'

    def request_escalated_in_progress(self):
        self.escalated_in_progress_date = date.today()
        workflow_id = self.env['ebs_mod.service.request.workflow'].search(
            [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
        if workflow_id:
            complete_date = workflow_id.complete_data
            if self.escalated_in_progress_date and complete_date:
                self.sla_days = self.get_date_difference(self.escalated_in_progress_date, complete_date, 1)
        self.status = 'escalated_progress'

    def request_escalated_in_complete(self):
        self.escalated_incomplete_date = date.today()
        self.end_date = date.today()
        workflow_id = self.env['ebs_mod.service.request.workflow'].search(
            [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
        if workflow_id:
            complete_date = workflow_id.complete_data
            if self.escalated_incomplete_date and complete_date:
                self.sla_days = self.get_date_difference(self.escalated_incomplete_date, complete_date, 1)
        self.status = 'escalated_incomplete'

    def request_escalated_complete(self):
        self.escalated_complete_date = date.today()
        self.end_date = date.today()
        workflow_id = self.env['ebs_mod.service.request.workflow'].search(
            [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
        if workflow_id:
            complete_date = workflow_id.complete_data
            if self.escalated_complete_date and complete_date:
                self.sla_days = self.get_date_difference(self.escalated_complete_date, complete_date, 1)
        self.status = 'escalated_complete'

    def request_incomplete(self):
        self.incomplete_date = date.today()
        self.end_date = date.today()
        workflow_id = self.env['ebs_mod.service.request.workflow'].search(
            [('service_request_id', '=', self.id), ('is_application_submission', '=', True)], limit=1)
        if workflow_id:
            complete_date = workflow_id.complete_data
            if self.incomplete_date and complete_date:
                self.sla_days = self.get_date_difference(self.incomplete_date, complete_date, 1)
        self.status = 'incomplete'

    def request_pending_payment(self):
        self.pending_payment_date = date.today()
        self.status = 'pending_payment'

    def request_progress(self):
        if self.env.user.has_group('ebs_qsheild_mod.qshield_account_manager') and not self.env.user.has_group(
                'ebs_qsheild_mod.qshield_operational_manager'):
            raise UserError('Account manager groups are not allowed to set in progress status')
        else:
            self.in_progress_date = date.today()
            self.status = 'progress'

    def request_draft(self):
        if len(self.service_flow_ids) == 0 and len(self.service_document_ids) == 0 and len(self.expenses_ids) == 0:
            self.start_date = None
            self.end_date = None
            self.draft_date = date.today()
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

    @api.constrains('name')
    def _check_service_request_duplicate_name(self):
        for record in self:
            if record.status not in 'draft':
                if self.env['ebs_mod.service.request'].search([('name', '=', record.name), ('id', '!=', record.id)]):
                    raise ValidationError(
                        _("The service request name is already used in another request please set a unique name"))


class ServiceRequestExpenses(models.Model):
    _name = "ebs_mod.service.request.expenses"
    _description = "Service Request Expenses"
    _order = 'date'

    def _domain_currency(self):
        currency_ids = []
        qatari_rials = self.env.ref('base.QAR')
        usd = self.env.ref('base.USD')
        if qatari_rials:
            currency_ids.append(qatari_rials.id)
        if usd:
            currency_ids.append(usd.id)
        return [('id', 'in', currency_ids)]

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
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
        domain=_domain_currency)
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
        default=0.0)

    date = fields.Date(
        string='Payment Date',
        required=True)

    payment_by = fields.Selection([('qnb_0023', 'QNB 0023'),
                                   ('qnb_0015', 'QNB 0015'),
                                   ('doha_2766', 'DOHA 2766'),
                                   ('doha_8705', 'DOHA 8705'),
                                   ('e_cash_4364', 'E-CASH 4364'),
                                   ('amex_6201', 'AMEX 6201'),
                                   ('amex_3004', 'AMEX 3004'),
                                   ('cash', 'CASH')],
                                  string='Payment By',
                                  required=True)
