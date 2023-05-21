# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from pytz import timezone


class RefuseQuotation(models.TransientModel):
    _name = 'refuse.quotation'
    _description = "Refuse Quotation"

    reason = fields.Char(string="Reason")

    def refuse_quotation(self):
        if self.env.context.get('active_id'):
            today = datetime.now()
            user_tz = self.env.user.tz or "UTC"
            today = timezone('UTC').localize(today).astimezone(timezone(user_tz))
            reason_date = today.strftime('%Y-%m-%d %H:%m:%s')
            sale_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            if sale_order.state == 'quotation_submit':
                if self.reason and sale_order.refuse_quotation_reason:
                    reason = sale_order.refuse_quotation_reason + '\n' + '=>' + ' ' + self.reason + " Refused by " + self.env.user.name + " " + reason_date
                else:
                    reason = '=>' + ' ' + self.reason + " Refused by " + self.env.user.name + " " + reason_date
                # approvers = sale_order.mapped('approver_ids').filtered(lambda approver: approver.status != 'refused')
                # for approver in approvers:
                #     approver.write({'status': 'refused'})
                sale_order.write({'state': 'draft', 'refuse_quotation_reason': reason})
            elif sale_order.state == 'agreement_submit':
                if self.reason and sale_order.refuse_agreement_reason:
                    reason = sale_order.refuse_agreement_reason + '\n' + '=>' + ' ' + self.reason + " Refused by " + self.env.user.name + " " + reason_date
                else:
                    reason = '=>' + ' ' + self.reason + " Refused by " + self.env.user.name + " " + reason_date
                # approvers = sale_order.mapped('approver_ids').filtered(lambda approver: approver.status != 'refused')
                # for approver in approvers:
                #     approver.write({'status': 'refused'})
                sale_order.write({'state': 'sale', 'refuse_agreement_reason': reason})
