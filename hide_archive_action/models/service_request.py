from odoo import models, fields, api, _


class EbsModServiceRequest(models.Model):
    _inherit = 'ebs_mod.service.request'

    def archive_services(self):
        action = self.env.ref('hide_archive_action.action_archive_service_request').read()[0]
        context = dict(self.env.context)
        context.update({'service_request_ids': self})
        action.update({'context': context})
        return action

    def unarchive_services(self):
        for record in self:
            if record.service_flow_ids:
                for workflow in record.service_flow_ids:
                    workflow.sudo().write({'active': True})
            record.sudo().write({'active': True})
