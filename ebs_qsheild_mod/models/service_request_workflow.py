from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)


class ServiceRequestWorkFlow(models.Model):
    _name = 'ebs_mod.service.request.workflow'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _description = "Service Request Workflow"
    _order = 'workflow_id '

    status_dict = {
        'new': 'New',
        'pending': 'Pending',
        'progress': 'In Progress',
        'hold': 'On Hold',
        'complete': 'Completed',
        'reject': 'Rejected',
        'cancel': 'Canceled'
    }

    service_request_id = fields.Many2one(
        comodel_name='ebs_mod.service.request',
        string='Service',
        required=True)

    def _get_workflow_domain(self):
        domain = [
            ('flow_type', '=', self.service_request_id.flow_type),
            ('service_type_id', '=', self.service_request_id.service_type_id.id)
        ]
        return domain

    workflow_id = fields.Many2one(
        comodel_name='ebs_mod.service.type.workflow',
        string='Workflow',
        required=True,

    )
    is_application_submission = fields.Boolean(
        related='workflow_id.is_application_submission', store=True,
        string='Is Application Submission')

    complete_data = fields.Date(compute='compute_submission_date', store=True)

    name = fields.Char(
        string='Name',
        related="workflow_id.name",
        store=True,
        required=False)

    due_date = fields.Datetime(
        string='Due Date',
        required=False)

    sequence = fields.Integer(
        string='Sequence',
        related="workflow_id.sequence",
        required=False)
    flow_type = fields.Selection(
        string='Workflow Type',
        selection=[('o', 'Online'),
                   ('m', 'Manual'), ],
        related="service_request_id.flow_type",
        required=False)
    service_type_id = fields.Many2one(
        comodel_name='ebs_mod.service.types',
        string='Service Type',
        required=False,
        related="service_request_id.service_type_id",
    )
    related_company = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        related="service_request_id.related_company_ro",
        required=False)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Related Contact',
        related="service_request_id.partner_id",
        required=False)

    start_count_flow = fields.Boolean(
        string='Start Count Flow',
        required=False,
        related="workflow_id.start_count_flow",
        store=True, readonly=False
    )
    status = fields.Selection(
        string='Status',
        selection=[('new', 'New'),
                   ('pending', 'Pending'),
                   ('progress', 'in Progress'),
                   ('hold', 'On Hold'),
                   ('complete', 'Completed'),
                   ('cancel', 'Cancelled'),
                   ('reject', 'Rejected'),
                   ],
        required=True)
    status_new = fields.Selection(selection=[('new', 'New')], string="Status")

    desc = fields.Text(
        string="Description",
        required=False)

    date = fields.Datetime(
        string='Status Last Updated',
        required=False)

    assign_to = fields.Many2one(
        comodel_name='res.users',
        string='Assign To',
        required=False,
        default=lambda self: self.env.user,
    )

    is_show_status = fields.Boolean('Is Show status', related='service_request_id.is_show_status')
    is_show_new_status = fields.Boolean('Is Show status', related='service_request_id.is_show_new_status')
    is_edit_status = fields.Boolean('Is Show status', related='service_request_id.is_edit_status')
    is_edit_status_new = fields.Boolean('Is Show status', related='service_request_id.is_edit_status_new')

    def send_notification(self):
        if self.workflow_id.is_application_submission:
            email_to_list = []
            email_list = []
            is_send_service_notification = self.env['ir.config_parameter'].sudo().get_param(
                'ebs_qsheild_mod.is_send_service_notification')
            workflow_status = dict(self._fields['status'].selection).get(self.status)
            if is_send_service_notification:
                email_to_list = self.env['ir.config_parameter'].sudo().get_param(
                    'ebs_qsheild_mod.send_notification_email')
                email_list = email_to_list.split(',')
                notification_users = self.env['res.users'].sudo().search([('email', 'in', email_list)])
                mail_activity_type = self.env.ref('ebs_qsheild_mod.notification_of_service_workflow_status').id
                self.service_request_id.with_context(status=workflow_status,
                                                     workflow=self.ids).create_schedule_activity(
                    mail_activity_type,
                    notification_users)
            template = self.env.ref('ebs_qsheild_mod.mail_template_of_notify_application_submission_complete',
                                    raise_if_not_found=False)
            outgoing_server = self.env['ir.mail_server'].sudo().search([('smtp_user', '!=', False)], limit=1)
            if not outgoing_server:
                logger.info("Please configure out going mail server")
            if not email_to_list:
                logger.info("Please configure recipient email in service settings")
            user_sudo = self.env.user
            service_status = dict(self.env['ebs_mod.service.request']._fields['status'].selection).get(
                self.service_request_id.status)
            if template:
                for email_to in email_list:
                    template.sudo().with_context(username=user_sudo.name, email=email_to,
                                                 email_from=outgoing_server.smtp_user,
                                                 service_status=service_status,
                                                 workflow_status=workflow_status).send_mail(
                        self._origin.id, force_send=True)

    @api.onchange('status_new')
    def get_status_new(self):
        for rec in self:
            rec.status = rec.status_new

    @api.onchange('due_date')
    def _due_date_on_change(self):
        if self.due_date:
            if self.env.company.disable_future_date_service:
                if self.due_date < datetime.now():
                    self.due_date = datetime.now()

    @api.depends('status')
    def compute_submission_date(self):
        for rec in self:
            if rec.is_application_submission and rec.status == 'complete':
                rec.complete_data = fields.Date.today()

    def create_service_activity(self):
        if self.due_date and self.assign_to:
            activity_type = self.env['mail.activity.type'].search([('name', '=', "To Do")], limit=1)
            self.activity_schedule(
                date_deadline=self.due_date,
                summary=self.workflow_id.name,
                note='',
                user_id=self.assign_to.id,
                activity_type_id=activity_type.id
            )
            message_id = self.env['message.wizard'].create({'message': _("Activity Created.")})
            return {
                'name': _('Success'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.wizard',
                # pass the id
                'res_id': message_id.id,
                'target': 'new'
            }
        else:
            raise ValidationError(_("Fill due date and assign to."))

    @api.model
    def create(self, values):
        res = super(ServiceRequestWorkFlow, self).create(values)
        if res.assign_to:
            res.push_notification_of_assing_user(res.assign_to)
        return res

    def write(self, vals):
        if vals.get('status', False):
            if vals['status'] != self.status:
                self.service_request_id.message_post(
                    body="Workflow " + self.workflow_id.name + " status changed from " + self.status_dict[
                        self.status] + " to " + self.status_dict[
                             vals['status']] + ".")
        res = super(ServiceRequestWorkFlow, self).write(vals)
        is_send_service_notification = self.env['ir.config_parameter'].sudo().get_param(
            'ebs_qsheild_mod.is_send_service_notification')
        if vals.get('status') == 'complete' and self.status == 'complete' and is_send_service_notification:
            self.send_notification()
        if vals.get('status') == 'cancel' and self.status == 'cancel' and is_send_service_notification:
            self.send_notification()
        if vals.get('status') == 'reject' and self.status == 'reject' and is_send_service_notification:
            self.send_notification()
        if vals.get('assign_to', False):
            assign_user = self.env['res.users'].browse(vals.get('assign_to'))
            self.push_notification_of_assing_user(assign_user)
        if res:
            if vals.get('status', False):
                self.date = datetime.today()
                if self.start_count_flow and not self.service_request_id.start_date:
                    self.service_request_id.is_started = True
                    self.service_request_id.start_date = datetime.today()
                    self.service_request_id.estimated_end_date = (
                            datetime.now().date() + timedelta(days=(self.service_request_id.sla_max or 0)))
                # if vals['status'] == 'progress':
                #     if self.start_count_flow:
                #         self.service_request_id.start_date = datetime.today()
                # if vals['status'] == 'complete':
                #     if self.start_count_flow and not self.service_request_id.start_date:
                #         self.service_request_id.start_date = datetime.today()

    # def unlink(self):
    #     for rec in self:
    #         if rec.service_request_id.status == 'progress':
    #             if self.status != 'pending':
    #                 raise ValidationError(_("Cannot Delete, service in progress."))
    #      return super(ServiceRequestWorkFlow, rec).unlink()

    def push_notification_of_assing_user(self, user):
        name = '#' + self.env.user.partner_id.name + ', ' + user.partner_id.name
        channel = self.env['mail.channel'].sudo().search(
            [('name', '=', name)])
        if not channel:
            channel = self.env['mail.channel'].sudo().create({
                'name': name,
                'description': False,
                'alias_contact': 'followers',
                'channel_type': 'chat',
                'public': 'private'
            })
        if channel.channel_last_seen_partner_ids:
            partner_list = [user.partner_id, self.env.user.partner_id]
            for partner in partner_list:
                if len(partner_list) != channel.channel_last_seen_partner_ids:
                    available_partner = channel.channel_last_seen_partner_ids.filtered(
                        lambda s: s.partner_id == partner)
                    if not available_partner:
                        channel.write({'channel_last_seen_partner_ids': [(0, 0, {'partner_id': partner.id,
                                                                                 'partner_email': partner.email})
                                                                         ]})
        else:
            channel.write({'channel_last_seen_partner_ids': [(0, 0, {'partner_id': user.partner_id.id,
                                                                     'partner_email': user.partner_id.email}),
                                                             (0, 0, {'partner_id': self.env.user.partner_id.id,
                                                                     'partner_email': self.env.user.partner_id.email})
                                                             ]})
        message_vals = {
            'author_id': self.env.user.partner_id.id,
            'email_from': self.env.user.partner_id.email or '',
            'model': 'mail.channel',
            'res_id': channel.id,
            'body': 'Hello, %s service workflow assign you.' % self.name,
            'message_type': 'comment',
            'subtype_id': self.env.ref('mail.mt_comment').id,
            'partner_ids': [(4, user.partner_id.id)],
            'reply_to': user.partner_id.email,
        }
        message = self.env['mail.message'].sudo().create(message_vals)
        notifications = channel._channel_message_notifications(message)
        body = 'Dear %s,<br/> You have a new task assigned to you <br/> Task Name: %s <br/> Service Request Number: %s ' \
               '<br/><br/> Regards,<br/>ODOO Notification Service' % (
                   user.name, self.name, self.service_request_id.name)
        channel.message_post(
            body=body, message_type='comment',
            subtype='mail.mt_comment', author_id=SUPERUSER_ID,
            notification_ids=notifications)
