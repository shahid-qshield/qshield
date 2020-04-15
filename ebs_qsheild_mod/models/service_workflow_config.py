from odoo import models, fields, api, _


class ServiceWorkflowConfig(models.Model):
    _name = "ebs_mod.service.workflow.config"
    _description = "Service Workflow Configuration"
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

    _sql_constraints = [
        ('service_type_flow_name_type_unique', 'unique (name,flow_type)',
         'Name and type combination must be unique !')
    ]
