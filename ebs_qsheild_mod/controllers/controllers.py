# -*- coding: utf-8 -*-
from odoo import http

# class EbsQsheildMod(http.Controller):
#     @http.route('/ebs_qsheild_mod/ebs_qsheild_mod/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/ebs_qsheild_mod/ebs_qsheild_mod/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('ebs_qsheild_mod.listing', {
#             'root': '/ebs_qsheild_mod/ebs_qsheild_mod',
#             'objects': http.request.env['ebs_qsheild_mod.ebs_qsheild_mod'].search([]),
#         })

#     @http.route('/ebs_qsheild_mod/ebs_qsheild_mod/objects/<model("ebs_qsheild_mod.ebs_qsheild_mod"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('ebs_qsheild_mod.object', {
#             'object': obj
#         })