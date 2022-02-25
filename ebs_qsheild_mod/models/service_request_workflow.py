from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, date


class ServiceRequestWorkFlow(models.Model):
    _name = 'ebs_mod.service.request.workflow'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _description = "Service Request Workflow"
    _order = 'workflow_id '

    status_dict = {
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
        selection=[('pending', 'Pending'),
                   ('progress', 'in Progress'),
                   ('hold', 'On Hold'),
                   ('complete', 'Completed'),
                   ('cancel', 'Cancelled'),
                   ('reject', 'Rejected'),
                   ],
        required=True, default='pending')

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

    def send_notification(self):
        if self.workflow_id.is_application_submission:
            template = self.env.ref('ebs_qsheild_mod.mail_template_of_notify_application_submission_complete',
                                    raise_if_not_found=False)
            user_sudo = self.env.user
            if template:
                if self.assign_to and self.service_request_id:
                    template.sudo().with_context(username=user_sudo.name, email=self.assign_to.work_email).send_mail(
                        self._origin.id, force_send=True)
                if self.service_request_id:
                    template.sudo().with_context(username=user_sudo.name,
                                                 email=self.service_request_id.account_manager.work_email).send_mail(
                        self._origin.id, force_send=True)

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

    def write(self, vals):
        if vals.get('status', False):
            if vals['status'] != self.status:
                self.service_request_id.message_post(
                    body="Workflow " + self.workflow_id.name + " status changed from " + self.status_dict[
                        self.status] + " to " + self.status_dict[
                             vals['status']] + ".")
        res = super(ServiceRequestWorkFlow, self).write(vals)
        if vals.get('status') == 'complete' and self.status == 'complete':
            self.send_notification()
        if vals.get('status') == 'cancel' and self.status == 'cancel':
            self.send_notification()
        if vals.get('status') == 'reject' and self.status == 'reject':
            self.send_notification()
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
