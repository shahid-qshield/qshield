# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError, MissingError


class CustomerPortal(CustomerPortal):

    @http.route('/reject/<int:sale_id>', type="http", website=True, auth='public')
    def sale_record_reject(self, sale_id, **post):
        sale_rec = request.env['sale.order'].sudo().browse(sale_id)
        sale_rec.sudo().with_context(from_portal=True).action_cancel()
        return request.render("qshield_crm.quotation_reject_template")

    @http.route('/approve/<int:sale_id>', type="http", website=True, auth='public')
    def sale_record_approve(self, sale_id, **post):
        sale_rec = request.env['sale.order'].sudo().browse(sale_id)
        sale_rec.sudo().with_context(from_portal=True).action_confirm()
        return request.render("qshield_crm.quotation_approve_template")


class PortalAccount(PortalAccount):
    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=invoice_sudo, report_type=report_type,
                                     report_ref='qshield_crm.account_expense_invoices',
                                     download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual,
                                                                         invoice_sudo.currency_id, country_id)

        return request.render("account.portal_invoice_page", values)
