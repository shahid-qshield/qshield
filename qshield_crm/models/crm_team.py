# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    @api.model
    def action_your_pipeline(self):
        if self.env.user.has_group('qshield_crm.qshield_crm_sales_person') or self.env.user.has_group(
                'qshield_crm.qshield_crm_management'):
            res = super(CrmTeam, self).action_your_pipeline()
            return res
        else:
            actions = self.env.ref('crm.crm_lead_all_leads').read()[0]
            return actions
