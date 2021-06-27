from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import io
import xlsxwriter
import base64

from datetime import date, datetime, timedelta
from odoo import models, fields, api, _


class SaleExcelReportController(http.Controller):

    def get_date_difference(self, start, end, ):
        count = 0
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(str(start), fmt)
        d2 = datetime.strptime(str(end), fmt)
        if d2 > d1:
            count = (d2 - d1).days
        return count

    @http.route('/document/excel_report', type='http', auth="user", csrf=False)
    @serialize_exception
    def get_sale_excel_report(self, **args):
        print('khaled')
        fmt = '%Y-%m-%d'
        response = request.make_response(
            None,
            headers=[
                ('Content-Type', 'application/vnd.ms-excel'),
                ('Content-Disposition', content_disposition('Expiry Document  in Excel' + '.xlsx'))
            ]
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # create some style to set up the font type, the font size, the border, and the aligment
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})

        sheet = workbook.add_worksheet(name='Expiry Document  in Excel')
        print("sheet", sheet)
        sheet.merge_range('A1:E1', 'Automated Report For All Documents expiry date', title_style)

        sheet.write(1, 0, 'No.', header_style)
        sheet.write(1, 1, 'Client', header_style)
        sheet.write(1, 2, 'Employee Name', header_style)
        sheet.write(1, 3, 'Employee / Dependent', header_style)
        sheet.write(1, 4, 'Corporate Document', header_style)
        sheet.write(1, 5, 'Document Type', header_style)
        sheet.write(1, 6, 'Document Number', header_style)
        sheet.write(1, 7, 'Account Manager', header_style)
        sheet.write(1, 8, 'Remaining Days For Expiry', header_style)
        sheet.write(1, 9, 'Expiry Date', header_style)

        row = 2
        number = 1

        documents = request.env['documents.document'].search(
            [('active', '=', 'True'), ('renewed', '=', False), ('notify', '=', True), ],
            order='related_company ASC')
        if documents:
            items = []
            base_url = request.env['ir.config_parameter'].get_param('web.base.url')
            for document in documents:
                Remaining_Days_for_expiry = 0
                if document.expiry_date:
                    Remaining_Days_for_expiry = (
                            datetime.strptime(str(fields.Date.today()), fmt) - datetime.strptime(
                        str(document.expiry_date), fmt)).days
                document_days = 0
                if document.expiry_date:
                    document_days = self.get_date_difference(fields.Date.today(), document.expiry_date, )
                if document_days <= document.days_before_notifaction:
                    sheet.write(row, 0, number, text_style)
                    ##############################################
                    sheet.write(row, 1,
                                document.related_company.name if document.related_company else document.partner_id.name,
                                text_style)

                    ###############################
                    sheet.write(row, 2, document.partner_id.name, text_style)
                    #########################
                    sheet.write(row, 3, document.partner_id.person_type if document.partner_id.person_type else " ",
                                text_style)
                    ######################
                    sheet.write(row, 4, "Yes" if document.partner_id.person_type == 'company' else "No",
                                number_style)
                    ############################
                    sheet.write(row, 5, document.document_type_id.name, number_style)
                    ##############################
                    sheet.write(row, 6, document.document_number, number_style)
                    ##################################
                    sheet.write(row, 7,
                                document.related_company.account_manager.name if document.related_company.account_manager else " ",
                                number_style)
                    ###############################
                    sheet.write(row, 8, Remaining_Days_for_expiry, number_style)
                    #########################
                    sheet.write(row, 9, fields.Date.to_string(document.expiry_date) if document.expiry_date else " ",
                                number_style)

                    # sheet.cell(row=row, column=2).hyperlink = str(
                    #     base_url) + '/web#id={id}&action={action_id}&model=documents.document&view_type=form'.format(
                    #     id=document.id, action_id=request.env.ref('documents.document_action').id
                    # )
                    # sheet.cell(row=row, column=2).value = document.partner_id.name
                    # sheet.cell(row=row, column=2).style = "Hyperlink"

                    row += 1
                    number += 1

        # return the excel file as a response, so the browser can download it
        workbook.close()
        output.seek(0)

        response.stream.write(output.read())
        base64.b64encode(output.read())
        output.close()

        return response
