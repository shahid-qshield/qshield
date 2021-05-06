# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta


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
        related="partner_id.date_stop_renew")
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

    @api.constrains('document_number')
    def _check_document_number(self):
        for rec in self:
            if len(self.env['documents.document'].search(
                    [('document_number', '=', rec.document_number), ('active', '=', True), ('id', '!=', rec.id)])) != 0:
                raise ValidationError(_("Document Number and Document Type Combination must be unique !"))

    def get_date_difference(self, start, end, ):
        count = 0
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(str(start), fmt)
        d2 = datetime.strptime(str(end), fmt)
        # if d2 > d1:
        count = (d2 - d1).days
        return count

    def notify_expired_document(self):
        group_companies = self.read_group(
            domain=[('related_company.account_manager', '!=', False)],
            fields=[],
            groupby=['related_company'])
        for company in group_companies:
            documents = self.search([('active', '=', 'True'), ('renewed', '=', False), ('notify', '=', True),
                                     ('related_company', '=', company['related_company'][0]), ])
            if documents:
                items = []
                account_manager = None
                company_name = None
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                for document in documents:
                    company_name = document.related_company.name
                    account_manager = document.related_company.account_manager
                    document_days = 0
                    if document.expiry_date:
                        document_days = self.get_date_difference(fields.Date.today(), document.expiry_date)
                    if 0 <= document_days <= document.days_before_notifaction:
                        items.append(
                            {
                                'Employee_Name': document.partner_id.name,
                                'Employee_Type': document.person_type,
                                'Document_Type': document.document_type_id.name,
                                'Document_Number': document.document_number,
                                'Expiration_Date': document.expiry_date,
                                'Document_url': str(
                                    base_url) + '/web#id={id}&action={action_id}&model=documents.document&view_type=form'.format(
                                    id=document.id, action_id=self.env.ref('documents.document_action').id
                                ),
                            }
                        )
                body = ''
                if items:
                    for doc in items:
                        body += " <tr> <th scope='row'>{}</th> ".format(doc['Employee_Name'])
                        body += "<th scope='row'>{}</th>".format(doc['Employee_Type'])
                        body += " <th scope='row'>{}</th>".format(doc['Document_Type'])
                        body += "<th scope='row'>{}</th>".format(doc['Document_Number'])
                        body += "<th scope='row'>{}</th>".format(doc['Expiration_Date'])
                        body += '''<th>'<a href="{url}" target="_blank">{name}</a></th></tr> '''.format(
                            url=doc['Document_url'],
                            name=doc['Employee_Name'])

            mail = self.env['mail.mail'].sudo().create({
                'subject': _('{} / Documents Expiration.'.format(
                    company_name)),
                'email_from': self.env.user.partner_id.email,
                'author_id': self.env.user.partner_id.id,
                'email_to': account_manager.user_id.email,
                'body_html': " Dear {}, <br/> ".format(
                    company_name) + '<br/>' +
                             " <strong> Below is the list of document Subject to expiry :  </strong> <br/>" + '<br/>' +
                             '''
                             <table class='table'>
                                  <thead>
                                       <tr>
                                              <th scope="col">Employee Name</th>
                                              <th scope="col">Employee Type</th>
                                              <th scope="col">Document Type</th>
                                              <th scope="col">Document Number</th>
                                              <th scope="col">Expiration Date</th>
                                              <th scope="col">Document url</th>
                                       </tr>
                                  </thead>
                                  <tbody>''' + body + '''
                                                                    </tbody>
                                  
                              </table>
                             '''

                ,
            })
            mail.send()


def notify_document_before_expired_to_partner(self):
    group_companies = self.read_group(
        domain=[('related_company.account_manager', '!=', False)],
        fields=[],
        groupby=['partner_id'])
    for company in group_companies:
        # ('renewed', '=', False),
        documents = self.search([('active', '=', 'True'), ('notify', '=', True),
                                 ('partner_id', '=', company['partner_id'][0]), ])
        if documents:
            items = []
            account_manager = None
            partner_id = self.env['res.partner'].search([('id', '=', company['partner_id'][0])], limit=1)
            company_name = None
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            for document in documents:
                company_name = document.related_company.name
                account_manager = document.related_company.account_manager
                document_days = 0
                if document.expiry_date:
                    document_days = self.get_date_difference(fields.Date.today(), document.expiry_date, )
                if document_days <= document.days_before_notifaction:
                    items.append(
                        {
                            'Employee_Name': document.partner_id.name,
                            'Employee_Type': document.person_type,
                            'Document_Type': document.document_type_id.name,
                            'Document_Number': document.document_number,
                            'Expiration_Date': document.expiry_date,
                            'Document_url': str(
                                base_url) + '/web#id={id}&action={action_id}&model=documents.document&view_type=form'.format(
                                id=document.id, action_id=self.env.ref('documents.document_action').id
                            ),
                        }
                    )
            body = ''
            if items:
                for doc in items:
                    contact_type_list = [('company', 'Company'),
                                         ('emp', 'Employee'),
                                         ('visitor', 'Visitor'),
                                         ('child', 'Dependent')]
                    contact_type_list = dict(contact_type_list)
                    body += "["
                    body += str(doc['Employee_Name'])
                    body += '/'
                    body += contact_type_list[str(doc['Employee_Type'])]
                    body += '/'
                    body += str(doc['Document_Type'])
                    body += '/'
                    body += str(doc['Document_Number'])
                    body += '/'
                    body += str(doc['Expiration_Date'])
                    body += '/ <a href=\"'
                    body += str(doc['Document_url'])
                    body += '\" target="_blank">'
                    body += str(doc['Employee_Name'])
                    body += '</a>.'
                    body += "]<br/>"
                    body += '<br/>'
                    body += '<br/>'
                mail = self.env['mail.mail'].sudo().create({
                    'subject': _('{} / Documents Expiration.'.format(partner_id.name)),
                    'email_from': self.env.user.partner_id.email,
                    'author_id': self.env.user.partner_id.id,
                    'email_to': account_manager.user_id.email,
                    'body_html': " Dear {}, <br/> ".format(company_name) + '<br/>' +
                                 " These are expired to be documents"
                                 " that belongs to {partner} with full details <br/>".format(
                                     partner=partner_id.name)
                                 +
                                 '<br/>' +
                                 body
                    ,
                })
                mail.send()


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
        expiry_date = datetime.strptime(vals['expiry_date'], "%Y-%m-%d").date()
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


class DocumentsFolderCustom(models.Model):
    _inherit = 'documents.folder'
    is_default_folder = fields.Boolean(
        string='Is Default Folder',
        required=False
    )
