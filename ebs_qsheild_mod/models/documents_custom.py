# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import io
import xlsxwriter
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from odoo.tools import ormcache, formataddr


class DocumentsCustom(models.Model):
    _inherit = 'documents.document'
    _order = 'issue_date desc'

    # _sql_constraints = [
    #     ('document_number_document_type_unique',act 'unique (document_number,document_type_id)',
    #      'Document Number and Document Type Combination must be unique !'),
    # ]

    desc = fields.Text(
        string="Description",
        required=False)
    issue_date = fields.Date(
        string='Issued Date',
        required=False)
    expiry_date = fields.Date(
        required=False)

    document_number = fields.Char(
        string='Document Number',
        required=False)
    document_type_id = fields.Many2one(
        comodel_name='ebs_mod.document.types',
        string='Document Type',
        required=False)

    notify = fields.Boolean(
        string='Notified For Expiration',
        related='document_type_id.notify',
        store=True
    )

    days_before_notifaction = fields.Integer(
        string='Days Before Expiration',
        related='document_type_id.days_before_notifaction',
    )

    status = fields.Selection(
        string='Status',
        selection=[('na', 'N/A'),
                   ('active', 'Active'), ('expired', 'Expired')],
        default='na',
        required=False, )

    service_id = fields.Many2one(
        comodel_name='ebs_mod.service.request',
        string='Service',
        required=False, tracking=True)

    related_company = fields.Many2one(
        comodel_name='res.partner',
        string='Related Company',
        store=True,
        related="partner_id.related_company")

    related_contact = fields.Many2one(
        comodel_name='res.partner',
        string='Related Contact',
        related="partner_id.parent_id")
    date_stop_renew = fields.Date(
        string='Do Not Renew After',
        required=False,
        related="partner_id.date_stop_renew", store=True)

    person_type = fields.Selection(
        string='Person Type',
        selection=[
            ('company', 'Company'),
            ('emp', 'Employee'),
            ('visitor', 'Visitor'),
            ('child', 'Dependent')],
        store=True,
        related="partner_id.person_type"
    )

    sponsor = fields.Many2one(
        comodel_name='res.partner',
        string='Sponsor',
        required=False,
        readonly=True,
        store=True,
        related="partner_id.sponsor")

    renewed = fields.Boolean(
        string='Renewed',
        required=False,
        default=False)

    archive_from_contact = fields.Boolean()
    expiration_days = fields.Integer(string="Expiration Days", compute="compute_expiration_days")
    related_document_type = fields.Selection(compute="_compute_related_document_type", store=True,
                                             selection=[('passport', 'Passport'), ('qatar_id', 'Qatar ID')])

    @api.depends()
    def compute_expiration_days(self):
        for record in self:
            if record.expiry_date and record.expiry_date > date.today():
                record.expiration_days = record.get_date_difference(date.today(), record.expiry_date)
            else:
                record.expiration_days = 0

    @api.constrains('document_number')
    def _check_document_number(self):
        for rec in self:
            if len(self.env['documents.document'].search(
                    [('document_number', '=', rec.document_number), ('active', '=', True), ('id', '!=', rec.id)])) != 0:
                raise ValidationError(_("Document Number and Document Type Combination must be unique !"))

    @api.depends('document_type_id', 'document_type_id.type')
    def _compute_related_document_type(self):
        for rec in self:
            if rec.document_type_id:
                rec.related_document_type = rec.document_type_id.type

    def get_date_difference(self, start, end, ):
        count = 0
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(str(start), fmt)
        d2 = datetime.strptime(str(end), fmt)
        if d2 > d1:
            count = (d2 - d1).days
        return count

    def notify_expired_document(self):
        group_companies = self.read_group(
            domain=[('related_company', '!=', False), ('partner_id', '!=', False)],
            fields=[],
            groupby=['related_company'])
        recipient_emails_for_document_expiry = self.env['ir.config_parameter'].sudo().get_param(
            'ebs_qsheild_mod.recipient_emails_for_document_expiry')
        email_list = recipient_emails_for_document_expiry.split(',')
        if not recipient_emails_for_document_expiry:
            pass
        for company in group_companies:
            # if company['related_company'] is None:
            #     print('---------------------------------')
            documents = self.search([('active', '=', 'True'), ('renewed', '=', False), ('notify', '=', True), '|',
                                     ('related_company', '=', company['related_company'][0]),
                                     ('partner_id', '=', company['related_company'][0])])
            document_types = documents.mapped('document_type_id')
            if documents and document_types:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                for document_type in document_types:
                    if document_type.expiry_configuration_ids:
                        filtered_documents = documents.filtered(lambda s: s.document_type_id == document_type)
                        if filtered_documents:
                            for configuration_id in document_type.expiry_configuration_ids:
                                expired_documents = filtered_documents.filtered(
                                    lambda s: s.expiration_days == configuration_id.days_before_notification)
                                items = []
                                account_manager = None
                                company_name = None
                                for document in expired_documents:
                                    company_name = False
                                    if document.related_company:
                                        company_name = document.related_company.name
                                    else:
                                        company_name = document.partner_id.name
                                    account_manager = document.related_company.account_manager
                                    document_days = 0
                                    person_type = ''
                                    if document.person_type:
                                        person_type = dict(document.partner_id._fields['person_type'].selection).get(
                                            document.person_type)
                                    items.append(
                                        {
                                            'document_number': document.document_number,
                                            'document_type': document.document_type_id.name,
                                            'contact': document.partner_id.name or '',
                                            'person_type': person_type,
                                            'expiration_date': document.expiry_date,
                                            'related_contact': document.related_contact.name or '',
                                            'date_stop_renew': document.date_stop_renew or '',
                                            'Document_url': str(
                                                base_url) + '/web#id={id}&action={action_id}&model=documents.document&view_type=form'.format(
                                                id=document.id, action_id=self.env.ref('documents.document_action').id
                                            ),
                                        }
                                    )
                                body = ''
                                if items:
                                    table_body = ''
                                    for doc in items:
                                        table_body = ''
                                        table = ''
                                        table += "<table class='table_1'>"
                                        document_url = '''<a href="{url}" target="_blank">{name}</a>'''.format(
                                            url=doc['Document_url'],
                                            name=doc['document_number'])
                                        table_body += "<tr><td>Document Number</td><td>{}</td></tr>".format(
                                            document_url)
                                        table_body += "<tr><td>Document Type</td><td>{}</td></tr>".format(
                                            doc['document_type'])
                                        table_body += "<tr><td>Contact</td><td>{}</td></tr>".format(doc['contact'])
                                        table_body += "<tr><td>Type of contact</td><td>{}</td></tr>".format(
                                            doc['person_type'])
                                        table_body += "<tr><td>Expires on</td><td>{}</td></tr>".format(
                                            doc['expiration_date'])
                                        table_body += "<tr><td>Related Contact</td><td>{}</td></tr>".format(
                                            doc['related_contact'])
                                        table_body += "<tr><td>Don’t Renew After</td><td>{}</td></tr>".format(
                                            doc['date_stop_renew'])
                                        table += table_body + '</table> <br/>'
                                        body += table
                                        # body += '''<th><a href="{url}" target="_blank">{name}</a></th></tr> '''.format(
                                        #     url=doc['Document_url'],
                                        #     name=doc['Employee_Name'])
                                    for email in email_list:
                                        mail = self.env['mail.mail'].sudo().create({
                                            'subject': _('{} - {} - {}'.format(
                                                company_name, document_type.name,
                                                configuration_id.days_before_notification)),
                                            'email_from': self.env.user.partner_id.email,
                                            'author_id': self.env.user.partner_id.id,
                                            'email_to': email,
                                            # 'email_from': self.env.company.email or self.env.user.partner_id.email,
                                            # 'author_id': self.env.company.partner_id.id,
                                            # 'email_to': account_manager.user_id.partner_id.email,
                                            'body_html': "<style>"
                                                         '''.table_1 {
                                                         table-layout: fixed;
                                                         }
                                                         .table_1 td,.table_1 th {
                                                         border: 2px solid #454141;
                                                         text-align: left;
                                                         padding: 4px;
                                                         }
                                                         .table_1 th{
                                                         width: 250px;
                                                         }
                                                         .table_1 td p{
                                                         width: 99%;
                                                         }''' + "</style>" +
                                                         " Dear {}, <br/> ".format(
                                                             company_name) + '<br/>' +
                                                         " <strong> Below is the list of document Subject to expiry :  </strong> <br/>" + '<br/>' + body
                                            ,
                                        })
                                        mail.send()
                            # if items:
                            #     for doc in items:
                            #         body += " <tr> <th scope='row'>{}</th> ".format(doc['document_number'])
                            #         body += "<th scope='row'>{}</th>".format(doc['document_type'])
                            #         body += " <th scope='row'>{}</th>".format(doc['contact'])
                            #         body += "<th scope='row'>{}</th>".format(doc['person_type'])
                            #         body += "<th scope='row'>{}</th>".format(doc['expiration_date'])
                            #         body += "<th scope='row'>{}</th>".format(doc['related_contact'])
                            #         body += "<th scope='row'>{}</th>".format(doc['date_stop_renew'])
                            #         body += '''<th><a href="{url}" target="_blank">{name}</a></th></tr> '''.format(
                            #             url=doc['Document_url'],
                            #             name=doc['Employee_Name'])
                            #     mail = self.env['mail.mail'].sudo().create({
                            #         'subject': _('{} - {} - {}'.format(
                            #             company_name,document_type.name,document_days)),
                            #         'email_from': self.env.user.partner_id.email,
                            #         'author_id': self.env.user.partner_id.id,
                            #         'email_to': 'crm@qshield.com',
                            #         # 'email_from': self.env.company.email or self.env.user.partner_id.email,
                            #         # 'author_id': self.env.company.partner_id.id,
                            #         # 'email_to': account_manager.user_id.partner_id.email,
                            #         'body_html':
                            #             " Dear {}, <br/> ".format(
                            #                 company_name) + '<br/>' +
                            #             " <strong> Below is the list of document Subject to expiry :  </strong> <br/>" + '<br/>' +
                            #             '''
                            #             <table class='table'>
                            #                  <thead>
                            #                       <tr>
                            #                              <th scope="col">Document Number</th>
                            #                              <th scope="col">Document Type</th>
                            #                              <th scope="col">Contact</th>
                            #                              <th scope="col">Type of contact</th>
                            #                              <th scope="col">Expires on</th>
                            #                              <th scope="col">Related Contact</th>
                            #                               <th scope="col">Don’t Renew After</th>
                            #                       </tr>
                            #                  </thead>
                            #                  <tbody>
                            #                        ''' + body + '''
                            #                             </tbody>
                            #                     </table>'''
                            #
                            #         ,
                            #     })
                            #     mail.send()

    def get_document_expiry_report(self, response):
        fmt = '%Y-%m-%d'
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        title_style = workbook.add_format({'font_name': 'Times', 'font_size': 14, 'bold': True, 'align': 'center'})
        header_style = workbook.add_format(
            {'font_name': 'Times', 'bold': True, 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'center'})
        text_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'left'})
        number_style = workbook.add_format(
            {'font_name': 'Times', 'left': 1, 'bottom': 1, 'right': 1, 'top': 1, 'align': 'right'})
        sheet = workbook.add_worksheet(name='Expiry Document in Excel')
        sheet.set_column('A1:K1', 25)
        sheet.merge_range('A1:K1', 'Automated Report For All Documents expiry date', title_style)
        # sheet.write(1, 0, 'No.', header_style)
        sheet.write(1, 0, 'Client', header_style)
        sheet.write(1, 1, 'Employee Name', header_style)
        sheet.write(1, 2, 'Status', header_style)
        sheet.write(1, 3, 'Employee / Dependent', header_style)
        sheet.write(1, 4, 'Related Contact', header_style)
        sheet.write(1, 5, 'Sponsor', header_style)
        sheet.write(1, 6, 'Document Type', header_style)
        sheet.write(1, 7, 'Document Number', header_style)
        sheet.write(1, 8, 'Account Manager', header_style)
        sheet.write(1, 9, 'Remaining Days For Expiry', header_style)
        sheet.write(1, 10, 'Do Not Renew After', header_style)
        sheet.write(1, 11, 'Expiry Date', header_style)
        row = 2
        number = 1
        documents = []
        documents.extend(self.env['documents.document'].search(
            [('active', '=', 'True'), ('renewed', '=', False), ('date_stop_renew', '=', False),
             ('notify', '=', True), ],
            order='related_company ASC'))
        excluded_company_list = self.env['excluded.company'].search([])
        excluded_company_ids = excluded_company_list.mapped('related_companies')
        partners = self.env['res.partner'].search([])
        for partner in partners:
            if partner.date_stop_renew:
                documents.extend(self.env['documents.document'].search(
                    [
                        ('active', '=', 'True'), ('renewed', '=', False), ('partner_id', '=', partner.id),
                        ('expiry_date', '<', partner.date_stop_renew), ('date_stop_renew', '!=', False),
                        ('notify', '=', True)
                    ], order='related_company ASC'))
        documents.sort(key=lambda x: x.related_company, reverse=True)
        if documents:
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            for document in documents:
                if document.related_company.id not in excluded_company_ids.ids:
                    Remaining_Days_for_expiry = 0
                    if document.expiry_date:
                        Remaining_Days_for_expiry = (
                                datetime.strptime(str(document.expiry_date), fmt) - datetime.strptime(
                            str(fields.Date.today()), fmt)).days
                    document_days = 0
                    if document.expiry_date:
                        document_days = self.get_date_difference(document.expiry_date, fields.Date.today(), )
                    if document_days <= document.days_before_notifaction:
                        # sheet.write(row, 0, number, text_style)
                        ##############################################
                        sheet.write(row, 0,
                                    document.related_company.name if document.related_company else document.partner_id.name,
                                    text_style)

                        ###############################
                        sheet.write_url(row=row, col=1, url=str(
                            base_url) + '/web#id={id}&action={action_id}&model=documents.document&view_type=form'.format(
                            id=document.id, action_id=self.env.ref('documents.document_action').id),
                                        string=document.partner_id.name if document.partner_id else "False")
                        #########################
                        status = ''
                        if Remaining_Days_for_expiry <= 0:
                            status = 'Expired'
                        if Remaining_Days_for_expiry > 0:
                            status = 'Active'
                        sheet.write(row, 2, status,
                                    text_style)
                        ######################
                        person = ' '
                        if document.person_type == "company":
                            person = 'Company'
                        if document.person_type == "emp":
                            person = 'Employee'
                        if document.person_type == "visitor":
                            person = 'Visitor'
                        if document.person_type == "child":
                            person = 'Dependent'
                        sheet.write(row, 3, person,
                                    text_style)
                        ######################
                        sheet.write(row, 4, document.related_contact.name if document.related_contact.name else ' ',
                                    text_style)
                        ############################
                        sheet.write(row, 5, document.sponsor.name, text_style)
                        ##############################
                        sheet.write(row, 6, document.document_type_id.name, text_style)
                        ##############################
                        sheet.write(row, 7, document.document_number, text_style)
                        ##################################
                        sheet.write(row, 8,
                                    document.related_company.account_manager.name if document.related_company.account_manager else " ",
                                    text_style)
                        ###############################
                        sheet.write(row, 9, Remaining_Days_for_expiry, text_style)
                        #########################
                        sheet.write(row, 10, fields.Date.to_string(
                            document.partner_id.date_stop_renew) if document.partner_id.date_stop_renew else " ",
                                    text_style)
                        #########################
                        sheet.write(row, 11,
                                    fields.Date.to_string(document.expiry_date) if document.expiry_date else " ",
                                    text_style)
                        row += 1
                        number += 1
        workbook.close()
        output.seek(0)
        generated_file = response.stream.write(output.read())
        output.close()

        return generated_file

    def notify_document_before_expired_to_partner(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url') + '/web/content/download/xlsx_reports/'
        link = "href = " + str(base_url)
        # emails = ['helpdesk@qshield.com', 'melkhatib@qshield.com']
        # partners = self.env['res.partner'].search([('account_manager', '!=', False)])
        # for partner in partners:
        #     if partner.account_manager.user_id.partner_id.email:
        #         emails.append(partner.account_manager.user_id.partner_id.email)
        # emails = set(emails)
        recipient_emails = self.env['ir.config_parameter'].get_param(
            'ebs_qsheild_mod.recipient_emails_for_document_expiry')
        # emails = set(recipient_emails.split(','))
        mail = self.env['mail.mail'].sudo().create({
            'subject': _('Documents Expiry.'),
            'email_from': self.env.user.partner_id.email,
            'author_id': self.env.user.partner_id.id,
            'email_to': recipient_emails,
            # 'email_to': ','.join(emails),
            # 'email_to': 'helpdesk@qshield.com',
            'body_html':
                " Dear(s), <br/><br/> "
                " <strong> Please find attached the list of documents subject to expire.  </strong> <br/>"
                """<div style="margin: 16px 0px 16px 0px;">
                        <a """ + link + """
                            style="background-color: #875A7B; padding: 8px 16px 8px 16px; text-decoration: none; color: #fff; border-radius: 5px; font-size:13px;">
                            Download Document
                        </a>
                        </div> <br/><br/> """
                                        " Regards,Odoo Notification Service.<br/><br/>"
            ,
        })
        mail.send()
        # mail.attachment_ids = [(6, 0, [data_id.id])]

    def name_get(self):
        result = []
        for rec in self:
            rec_name = ""
            if rec.document_number:
                rec_name = rec.document_number
            else:
                rec_name = rec.name
            result.append((rec.id, rec_name))
        return result

    def write(self, vals):
        # if vals.get('expiry_date', False):
        #     expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d").today().date()
        #     if expiry_date > datetime.today().date():
        #         vals['status'] = 'active'
        #     else:
        #         vals['status'] = 'expired'
        res = super(DocumentsCustom, self).write(vals)
        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise ValidationError(_("Expiry date is before issue date."))
        return res

    def check_document_expiry_date(self):
        for doc in self.env['documents.document'].search([('status', '=', 'active')]):
            if doc.expiry_date:
                if doc.expiry_date < datetime.today().date():
                    doc.status = 'expired'

    @api.model
    def create(self, vals):
        if vals.get('expiry_date', False):
            if type(vals['expiry_date']) == str:
                expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d").date()
            else:
                expiry_date = vals['expiry_date']
            if expiry_date > datetime.today().date():
                vals['status'] = 'active'
            else:
                vals['status'] = 'expired'
        else:
            vals['status'] = 'na'
        res = super(DocumentsCustom, self).create(vals)
        if res.expiry_date and res.issue_date:
            if res.expiry_date < res.issue_date:
                raise ValidationError(_("Expiry date is before issue date."))
        return res

    def preview_document(self):
        self.ensure_one()
        action = {
            'type': "ir.actions.act_url",
            'target': "_blank",
            'url': '/documents/content/preview/%s' % self.id
        }
        return action

    def access_content(self):
        return super(DocumentsCustom, self).access_content()

    def contact_archived_document_issue(self):
        contact_ids = self.env['res.partner'].sudo().search(
            [('active', '=', False)])
        for contact_id in contact_ids:
            documents = self.env['documents.document'].sudo().search(
                [('partner_id', '=', contact_id.id), ('active', '=', False)], order='expiry_date desc')
            document_types_list = []
            for document in documents:
                if not document.document_type_id.id in document_types_list:
                    document.write({'archive_from_contact': True})
                    document_types_list.append(document.document_type_id.id)
        return True


class DocumentsFolderCustom(models.Model):
    _inherit = 'documents.folder'
    is_default_folder = fields.Boolean(
        string='Is Default Folder',
        required=False
    )
