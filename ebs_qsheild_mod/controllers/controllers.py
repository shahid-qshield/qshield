# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, content_disposition
import os
import base64
from odoo.exceptions import AccessError


class QshieldController(http.Controller):

    def binary_content(self, id, env=None, field='datas', share_id=None, share_token=None,
                       download=False, unique=False, filename_field='name'):
        env = env or request.env
        record = env['documents.document'].browse(int(id))
        filehash = None

        if share_id:
            share = env['documents.share'].sudo().browse(int(share_id))
            record = share._get_documents_and_check_access(share_token, [int(id)], operation='read')
        if not record:
            return (404, [], None)

        # check access right
        try:
            last_update = record['__last_update']
        except AccessError:
            return (404, [], None)

        mimetype = False
        if record.type == 'url' and record.url:
            module_resource_path = record.url
            filename = os.path.basename(module_resource_path)
            status = 301
            content = module_resource_path
        else:
            status, content, filename, mimetype, filehash = env['ir.http']._binary_record_content(
                record, field=field, filename=None, filename_field=filename_field,
                default_mimetype='application/octet-stream')
        status, headers, content = env['ir.http']._binary_set_headers(
            status, content, filename, mimetype, unique, filehash=filehash, download=download)

        return status, headers, content

    def _get_file_response(self, id, field='datas', share_id=None, share_token=None):
        """
        returns the http response to download one file.

        """

        status, headers, content = self.binary_content(
            id, field=field, share_id=share_id, share_token=share_token, download=False)

        if status != 200:
            return request.env['ir.http']._response_by_status(status, headers, content)
        else:
            content_base64 = base64.b64decode(content)
            headers.append(('Content-Length', len(content_base64)))
            response = request.make_response(content_base64, headers)

        return response

    @http.route(['/documents/content/preview/<int:id>'], type='http', auth='user')
    def documents_content(self, id):
        return self._get_file_response(id)

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
