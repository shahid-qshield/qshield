# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import date
from odoo.http import request
from odoo import fields, http, _
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.exceptions import AccessError, MissingError
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import get_records_pager
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv import expression
import logging
import shutil
import tempfile
from base64 import b64decode
from os import remove

_logger = logging.getLogger(__name__)

class SaleCustomerPortalInherit(CustomerPortal):

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        try:
            order_sudo = self._document_check_access('sale.order', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type,
                                     report_ref='qshield_crm.quotation_report_custom', download=download)

        # use sudo to allow accessing/viewing orders for public user
        # only if he knows the private token
        # Log only once a day
        if order_sudo:
            now = fields.Date.today().isoformat()
            session_obj_date = request.session.get('view_quote_%s' % order_sudo.id)
            if isinstance(session_obj_date, date):
                session_obj_date = session_obj_date.isoformat()
            if session_obj_date != now and request.env.user.share and access_token:
                request.session['view_quote_%s' % order_sudo.id] = now
                body = _('Quotation viewed by customer %s') % order_sudo.partner_id.name
                _message_post_helper(
                    "sale.order",
                    order_sudo.id,
                    body,
                    token=order_sudo.access_token,
                    message_type="notification",
                    subtype="mail.mt_note",
                    partner_ids=order_sudo.user_id.sudo().partner_id.ids,
                )

        values = {
            'sale_order': order_sudo,
            'message': message,
            'token': access_token,
            'return_url': '/shop/payment/validate',
            'bootstrap_formatting': True,
            'partner_id': order_sudo.partner_id.id,
            'report_type': 'html',
            'action': order_sudo._get_portal_return_action(),
        }
        if order_sudo.company_id:
            values['res_company'] = order_sudo.company_id

        if order_sudo.has_to_be_paid():
            domain = expression.AND([
                ['&', ('state', 'in', ['enabled', 'test']), ('company_id', '=', order_sudo.company_id.id)],
                ['|', ('country_ids', '=', False), ('country_ids', 'in', [order_sudo.partner_id.country_id.id])]
            ])
            acquirers = request.env['payment.acquirer'].sudo().search(domain)

            values['acquirers'] = acquirers.filtered(
                lambda acq: (acq.payment_flow == 'form' and acq.view_template_id) or
                            (acq.payment_flow == 's2s' and acq.registration_view_template_id))
            values['pms'] = request.env['payment.token'].search([('partner_id', '=', order_sudo.partner_id.id)])
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(order_sudo.amount_total,
                                                                         order_sudo.currency_id,
                                                                         order_sudo.partner_id.country_id.id)

        if order_sudo.state in ('draft', 'sent', 'cancel'):
            history = request.session.get('my_quotations_history', [])
        else:
            history = request.session.get('my_orders_history', [])
        values.update(get_records_pager(history, order_sudo))

        return request.render('sale.sale_order_portal_template', values)

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
                                     report_ref='qshield_crm.account_expense_invoices_custom',
                                     download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        acquirers = values.get('acquirers')
        if acquirers:
            country_id = values.get('partner_id') and values.get('partner_id')[0].country_id.id
            values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual,
                                                                         invoice_sudo.currency_id, country_id)

        return request.render("account.portal_invoice_page", values)


class DownloadZipFile(http.Controller):

    @http.route("/web/attachment/download_zip_file", type="http", auth="user")
    def download_zip_file(self, **kwargs):
        """Download a zip file from an attachment"""
        attachment_ids = kwargs.get("attachment_ids")
        invoice_name = kwargs.get('invoice_name')
        attachment_ids = eval(attachment_ids)
        if len(attachment_ids) == 0:
            return
        if attachment_ids:
            attachment_ids = request.env["ir.attachment"].sudo().browse(attachment_ids)
            with tempfile.TemporaryDirectory() as attachment_temp_dir:
                for attachment in attachment_ids:
                    try:
                        with open(
                            f"{attachment_temp_dir}/{attachment.name}", "wb"
                        ) as af:
                            af.write(b64decode(attachment.datas))
                        af.close()
                    except Exception as e:
                        _logger.info(f"{e}")
                shutil.make_archive(
                    f"{attachment_temp_dir}", "zip", attachment_temp_dir
                )
                response = http.send_file(
                    f"{attachment_temp_dir}.zip",
                    filename=invoice_name,
                    as_attachment=True,
                )
                # shutil.rmtree(attachment_temp_dir, ignore_errors=True)
                # remove(f"{attachment_temp_dir}.zip")
                return response