# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class QshieldProposalReport(models.AbstractModel):
    _name = 'report.qshield_crm.report_qshield_proposal_quotation'
    _description = 'Proforma Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].browse(docids)
        consolidation_list = []
        for doc in docs:
            if doc.order_line:
                products = doc.order_line.mapped('product_id')
                service_types = self.env['ebs_mod.service.types'].search([('product_id', 'in', products.ids)])
                consolidations = service_types.mapped('consolidation_id')
                for consolidation in consolidations:
                    service_type_list = []
                    for service_type in service_types.filtered(lambda s: s.consolidation_id == consolidation):
                        line = doc.order_line.filtered(lambda m: m.product_id == service_type.product_id)
                        if line:
                            quantity = sum(line.mapped('product_uom_qty'))
                            price = sum(line.mapped('price_subtotal'))
                            service_type_list.append({'service_type_name': service_type.name,
                                                      'quantity': quantity,
                                                      'price': price
                                                      })

                    consolidation_list.append(
                        {'doc_id': doc.id,
                         'consolidation_name': consolidation.name, 'service_type_list': service_type_list})

        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order',
            'docs': docs,
            'proforma': True,
            'consolidation_list': consolidation_list
        }
