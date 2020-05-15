from odoo import models, fields, api, _


class ServiceTypes(models.Model):
    _name = 'ebs_mod.service.types'
    _description = "Service Types"

    _sql_constraints = [
        ('service_type_code_unique', 'unique (code)',
         'Code must be unique !'),
        ('service_type_name_unique', 'unique (name)',
         'Name must be unique !')
    ]

    code = fields.Char(
        string='Code',
        required=True)

    name = fields.Char(
        string='Name',
        required=True)
    sla = fields.Char(
        string='SLA - Working Days',
        required=False)

    sla_min = fields.Integer(
        string='SLA - Minimum Days',
        required=False)

    sla_max = fields.Integer(
        string='SLA - Maximum Days',
        required=False)



    for_company = fields.Boolean(
        string='For Company',
        required=False,
        default=False)

    for_employee = fields.Boolean(
        string='For Employee',
        required=False,
        default=False)

    for_visitor = fields.Boolean(
        string='For Visitor',
        required=False,
        default=False)

    for_dependant = fields.Boolean(
        string='For Dependant',
        required=False,
        default=False)

    for_miscellaneous = fields.Boolean(
        string='For Miscellaneous',
        required=False,
        default=False)
    for_not_miscellaneous = fields.Boolean(
        string='For Not Miscellaneous',
        required=False,
        default=False)

    workflow_online_ids = fields.One2many(
        comodel_name='ebs_mod.service.type.workflow',
        inverse_name='service_type_id',
        string='Workflow Online',
        required=False,
        domain=[('flow_type', '=', 'o')])

    workflow_manual_ids = fields.One2many(
        comodel_name='ebs_mod.service.type.workflow',
        inverse_name='service_type_id',
        string='Workflow Manual',
        required=False,
        domain=[('flow_type', '=', 'm')])

    @api.model
    def create(self, vals):
        res = super(ServiceTypes, self).create(vals)
        for rec in self.env['ebs_mod.service.workflow.config'].search([]):
            self.env['ebs_mod.service.type.workflow'].create({
                'name': rec.name,
                'sequence': rec.sequence,
                'flow_type': rec.flow_type,
                'start_count_flow': rec.start_count_flow,
                'service_type_id': res.id,
            })
        return res


class ServiceTypeWorkflow(models.Model):
    _name = "ebs_mod.service.type.workflow"
    _description = "Service Type Workflow"
    _order = "sequence"
    name = fields.Char(
        string='Name',
        required=True)
    sequence = fields.Integer(
        string='Sequence',
        required=True, default=0)
    flow_type = fields.Selection(
        string='Type',
        selection=[('o', 'Online'),
                   ('m', 'Manual'), ],
        required=True)

    start_count_flow = fields.Boolean(
        string='Start Count Flow',
        required=False,
        default=False)

    service_type_id = fields.Many2one(
        comodel_name='ebs_mod.service.types',
        string='Service_type',
        required=False)

    _sql_constraints = [
        ('service_type_flow_name_type_unique', 'unique (service_type_id,name,flow_type)',
         'Name and type combination must be unique !')
    ]
