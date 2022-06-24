# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


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
