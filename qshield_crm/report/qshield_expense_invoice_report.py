# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class QshieldProposalReport(models.AbstractModel):
    _name = 'report.qshield_crm.report_qshield_expense_invoice'
    _description = 'Expense Invoices'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        consolidation_list = []
        for doc in docs:
            print("data ",doc)

        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'proforma': True,
            'consolidation_list': consolidation_list
        }
