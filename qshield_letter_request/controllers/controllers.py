# -*- coding: utf-8 -*-
# from odoo import http


# class QshieldLetterRequest(http.Controller):
#     @http.route('/qshield_letter_request/qshield_letter_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/qshield_letter_request/qshield_letter_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('qshield_letter_request.listing', {
#             'root': '/qshield_letter_request/qshield_letter_request',
#             'objects': http.request.env['qshield_letter_request.qshield_letter_request'].search([]),
#         })

#     @http.route('/qshield_letter_request/qshield_letter_request/objects/<model("qshield_letter_request.qshield_letter_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('qshield_letter_request.object', {
#             'object': obj
#         })
