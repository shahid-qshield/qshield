# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models
from itertools import groupby


class QshieldProposalReport(models.AbstractModel):
    _name = 'report.qshield_crm.report_qshield_expense_invoice'
    _description = 'Expense Invoices'

    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        consolidation_list = []
        retainer_doc_dict = {}
        for doc in docs:
            in_scope_service = doc.invoice_line_ids.mapped('service_request_id').filtered(lambda s: s.is_in_scope)
            retainer_line_amount = []
            if in_scope_service:
                for contract, contract_in_scope_services in groupby(in_scope_service, key=lambda s: s.contract_id):
                    amount = 0.0
                    service_requests = list(contract_in_scope_services)
                    for service_request in service_requests:
                        move_line = doc.invoice_line_ids.filtered(
                            lambda s: s.service_request_id == service_request and not s.is_government_fees_line)
                        amount += sum(move_line.mapped('price_subtotal'))
                    line = {'contract_name': contract.name,
                            'contract': contract,
                            'service_requests': list(service_requests),
                            'contact_name': doc.partner_id.name,
                            'amount': amount}
                    retainer_line_amount.append(line)
                retainer_doc_dict.update({doc: retainer_line_amount})
            # contract_ids = in_scope_service.mapped('contract_id')
            # for contract_id in contract_ids:
            #     contracgt
            print("data ", doc)

        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'proforma': True,
            'consolidation_list': consolidation_list,
            'retainer_doc_dict': retainer_doc_dict
        }
