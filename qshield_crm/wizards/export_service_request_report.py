# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
import calendar
from odoo.exceptions import UserError
import xlsxwriter
import io
import base64


class ExportServiceRequest(models.TransientModel):
    _name = 'export.service.request'
    _description = "Export Service Request"

    def _default_end_date(self):
        last_day = calendar.monthrange(date.today().year, date.today().month)
        return date.today().replace(day=last_day[1])

    def _default_start_date(self):
        return date.today().replace(day=1)

    export_for_contact = fields.Selection([('all_contact', 'All Contacts'), ('specific_contact', 'Specific Contact')],
                                          default="all_contact")
    contact_ids = fields.Many2many('res.partner', string='Contacts')
    start_date = fields.Date(string="Start Date", default=_default_start_date)
    end_date = fields.Date(string="End date", default=_default_end_date)
    binary_data = fields.Binary("File")

    def print_xlsx_report(self):
        print('------------------------')
        domain = [('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        if self.contact_ids:
            domain.append(('partner_id', 'in', self.contact_ids.ids))
        service_request_ids = self.env['ebs_mod.service.request'].sudo().search(domain)
        if not service_request_ids:
            raise UserError('Service Record Not Found')
        filename = 'service_request.xlsx'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_format = workbook.add_format({'bold': True, 'font_size': 12, 'align': 'center'})  # for header
        title_format = workbook.add_format(
            {'bold': True, 'font_size': 21, 'align': 'center', 'color': 'blue'})  # for header
        format1 = workbook.add_format({'font_size': 10, 'align': 'center'})  # for lines
        sheet = workbook.add_worksheet('Service Request')  # creates a sheet named Reorder report
        sheet.set_column(0, 2, 30)
        sheet.set_column(4, 5, 30)
        sheet.set_column(3, 3, 20)
        sheet.set_column(7, 11, 25)
        # Header row for sheet
        sheet.write(0, 0, 'Company', header_format)
        sheet.write(0, 1, 'Contact', header_format)
        sheet.write(0, 2, 'Agreement', header_format)
        sheet.write(0, 3, 'Date', header_format)
        sheet.write(0, 4, 'Service Request (Service Type)', header_format)
        sheet.write(0, 5, 'Service request Number', header_format)
        sheet.write(0, 6, 'Status', header_format)
        sheet.write(0, 7, 'Government Fee', header_format)
        sheet.write(0, 8, 'Services Fee', header_format)
        sheet.write(0, 9, 'Invoice Number', header_format)
        sheet.write(0, 10, 'Invoice Status', header_format)
        sheet.write(0, 11, 'Receipt Attachment', header_format)
        if service_request_ids:
            row = 1
            for service_request_id in service_request_ids:
                contract_id = self.env['ebs_mod.contracts']
                invoice_id = self.env['account.move']
                if service_request_id.sale_order_id:
                    contract_id = self.env['ebs_mod.contracts'].search(
                        [('sale_order_id', '=', service_request_id.sale_order_id.id)])
                    if service_request_id.sale_order_id.invoice_term_ids:
                        invoice_term = service_request_id.sale_order_id.invoice_term_ids.filtered(lambda
                                                                                                      s: s.start_term_date <= service_request_id.date and s.end_term_date >= service_request_id.date and s.invoice_id)
                        if invoice_term:
                            invoice_id = invoice_term[0].invoice_id
                government_fees = sum(service_request_id.mapped('expenses_ids').mapped('amount'))
                attachment_ids = self.env['ir.attachment']
                if service_request_id.mapped('expenses_ids'):
                    attachment_ids = \
                        service_request_id.mapped('expenses_ids').filtered(lambda s: s.attachment_ids).mapped(
                            'attachment_ids')
                service_fees = service_request_id.sale_order_id.amount_total
                sheet.write(row, 0, service_request_id.related_company_ro.name, format1)
                sheet.write(row, 1, service_request_id.partner_id.name, format1)
                sheet.write(row, 2, contract_id.name if contract_id else '', format1)
                sheet.write(row, 3, service_request_id.date.strftime('%d %b %Y'), format1)
                sheet.write(row, 4,
                            service_request_id.service_type_id.name if service_request_id.service_type_id else '',
                            format1)
                sheet.write(row, 5,
                            service_request_id.name if service_request_id.name else '',
                            format1)
                sheet.write(row, 6,
                            service_request_id.status if service_request_id.status else '',
                            format1)
                sheet.write(row, 7,
                            government_fees if government_fees > 0 else '',
                            format1)
                sheet.write(row, 8,
                            service_fees if service_fees > 0 else '',
                            format1)
                sheet.write(row, 9,
                            invoice_id.name if invoice_id else '',
                            format1)
                sheet.write(row, 10,
                            invoice_id.state if invoice_id else '',
                            format1)

                if attachment_ids:
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    col = 11
                    for attachment_id in attachment_ids:
                        sheet.write_url(row=row, col=col, url=str(
                            base_url) + '/web/content/{id}?download=true'.format(id=attachment_id.id), tip='Click here',
                                        string='Attachment link')
                        col += 1
                row += 1
        workbook.close()
        output.seek(0)
        output = base64.encodestring(output.read())
        self.write({'binary_data': output})
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=export.service.request&field=binary_data&download=true&id=%s&filename=%s' % (
                self.id, filename),
            'target': 'new',
        }
