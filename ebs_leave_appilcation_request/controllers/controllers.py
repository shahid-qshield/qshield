# -*- coding: utf-8 -*-
# from odoo import http


# class EbsLeaveAppilcationRequest(http.Controller):
#     @http.route('/ebs_leave_appilcation_request/ebs_leave_appilcation_request/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ebs_leave_appilcation_request/ebs_leave_appilcation_request/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ebs_leave_appilcation_request.listing', {
#             'root': '/ebs_leave_appilcation_request/ebs_leave_appilcation_request',
#             'objects': http.request.env['ebs_leave_appilcation_request.ebs_leave_appilcation_request'].search([]),
#         })

#     @http.route('/ebs_leave_appilcation_request/ebs_leave_appilcation_request/objects/<model("ebs_leave_appilcation_request.ebs_leave_appilcation_request"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ebs_leave_appilcation_request.object', {
#             'object': obj
#         })
