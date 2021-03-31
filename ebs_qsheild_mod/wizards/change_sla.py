# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date


class ChangeSLAWizard(models.TransientModel):
    _name = 'change.sla.wizard'
    _description = "Change SLA Wizard"

    sla_min = fields.Integer(
        string='SLA - Minimum Days',
        required=True,
        readonly=False)

    sla_max = fields.Integer(
        string='SLA - Maximum Days',
        required=True,
        readonly=False)

    def action_ok(self):
        """ close wizard"""
        sr_id = self._context.get('active_id')
        record = self.env['ebs_mod.service.request'].browse(sr_id)
        for line in record:
            line.update({
                "sla_min": self.sla_min,
                "sla_max": self.sla_max,
            })
            if line.sla_max:
                max_days = timedelta(days=record.sla_max)
                today = fields.Date.today()
                if record.progress_date:
                    if (today - max_days) < line.progress_date:
                        line.write({'status_sla': 'normal'})
                    else:
                        line.write({'status_sla': 'exceeded'})
