from odoo import http
from odoo.http import content_disposition, request

from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
import io
import xlsxwriter


class XLSXReportController(http.Controller):

    @http.route('/web/content/download/xlsx_reports/', type='http', csrf=False)
    def get_report_xlsx(self, **kw):
        response = request.make_response(
            None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                     ('Content-Disposition', content_disposition('Expiry Document in Excel' + '.xlsx'))
                     ]
        )
        request.env['documents.document'].get_document_expiry_report(response)
        return response
