from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceRequest(models.Model):
    _name = 'ebs_mod.service.request'
    _description = "Service Request"
    _order = 'date desc'

    code = fields.Char(
        string='Code',
        required=False)
    name = fields.Char(
        string='Name',
        required=False,
        default='/'
    )

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

    related_company_ro = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        readonly=True
    )

    related_company = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
    )

    date = fields.Date(
        string='Date',
        required=True
    )
    contract_id = fields.Many2one(
        comodel_name='ebs_mod.contracts',
        string='Contract',
        required=True,
        domain=[('id', '=', -1)]
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        required=True,
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
        required=False,
        related="partner_id.phone")

    mobile = fields.Char(
        string='Mobile',
        required=False,
        related="partner_id.mobile")

    is_miscellaneous = fields.Boolean(
        string='Is Miscellaneous',
        required=False,
        related="partner_id.is_miscellaneous"
    )

    email = fields.Char(
        string='Email',
        required=False,
        related="partner_id.email")

    desc = fields.Text(
        string="Description",
        required=False)
    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
                   ('progress', 'In Progress'),
                   ('complete', 'Completed'),
                   ('cancel', 'Canceled')],
        required=False,
        default='draft')

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

    @api.model
    def create(self, vals):
        res = super(ServiceRequest, self).create(vals)
        return res

    def write(self, vals):
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

        if self.flow_type == 'o':
            flow_list = self.service_type_id.workflow_online_ids
        else:
            flow_list = self.service_type_id.workflow_manual_ids

        for flow in flow_list:
            self.env['ebs_mod.service.request.workflow'].create({
                'service_request_id': self.id,
                'workflow_id': flow.id,
            })

    def request_cancel(self):
        self.status = 'cancel'

    def request_draft(self):

        if len(self.service_flow_ids) == 0:
            self.start_date = None
            self.end_date = None
            self.status = 'draft'
        else:
            raise ValidationError(_("Delete all Workflow."))

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.name))
        return result


class ServiceRequestWorkFlow(models.Model):
    _name = 'ebs_mod.service.request.workflow'
    _description = "Service Request Workflow"
    _order = 'workflow_id desc'

    _sql_constraints = [
        ('service_workflow_unique', 'unique (service_request_id,workflow_id)',
         'Workflow already added!')
    ]

    service_request_id = fields.Many2one(
        comodel_name='ebs_mod.service.request',
        string='Workflow',
        required=True)

    workflow_id = fields.Many2one(
        comodel_name='ebs_mod.service.type.workflow',
        string='Workflow',
        required=True)

    sequence = fields.Integer(
        string='Sequence',
        related="workflow_id.sequence",
        required=False)

    start_count_flow = fields.Boolean(
        string='Start Count Flow',
        required=False,
        related="workflow_id.start_count_flow")

    status = fields.Selection(
        string='Status',
        selection=[('progress', 'in Progress'),
                   ('complete', 'Completed'), ],
        required=True, default='progress')

    desc = fields.Text(
        string="Description",
        required=False)

    date = fields.Date(
        string='Status Last Updated',
        required=False)

    assign_to = fields.Many2one(
        comodel_name='res.users',
        string='Assign To',
        required=False, default=lambda self: self.env.user)

    def write(self, vals):
        res = super(ServiceRequestWorkFlow, self).write(vals)
        if res:
            complete = True
            for flow in self.service_request_id.service_flow_ids:
                if flow.status == 'progress':
                    complete = False
                    break
            if complete:
                self.service_request_id.status = 'complete'

    def unlink(self):
        if self.service_request_id.status == 'progress':
            raise ValidationError(_("Cannot Delete, service in progress."))
        return super(ServiceRequestWorkFlow, self).unlink()


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
