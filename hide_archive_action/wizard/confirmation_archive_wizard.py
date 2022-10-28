from odoo import models, fields, api, _


class ConfirmationArchive(models.TransientModel):
    _name = 'confirmation.archive.wizard'

    is_workflow_archive = fields.Boolean(string="Is workflow archive")

    def archive_service(self):
        if self._context.get('active_ids'):
            service_request_ids = self.env['ebs_mod.service.request'].browse(self._context.get('active_ids'))
            for record in service_request_ids:
                if self.is_workflow_archive and record.service_flow_ids:
                    for workflow in record.service_flow_ids:
                        workflow.sudo().write({'active': False})
                record.sudo().write({'active': False})

