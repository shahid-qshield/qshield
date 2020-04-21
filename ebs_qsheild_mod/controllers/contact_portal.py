from odoo import http
from odoo.exceptions import AccessError, MissingError, UserError
from odoo.http import request
from odoo.tools.translate import _
from odoo.addons.portal.controllers.portal import pager as portal_pager, CustomerPortal
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.osv.expression import OR


class ContactPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(ContactPortal, self)._prepare_portal_layout_values()
        values['payment_count'] = request.env['ebs_mod.contact.payment'].search_count(
            [('partner_id', '=', request.env.user.partner_id.id)])
        if values.get('sales_user', False):
            values['title'] = _("Salesperson")
        return values

    @http.route(['/my/payments', '/my/payments/page/<int:page>'], type='http', auth="user", website=True)
    def my_contact_payment(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content',
                           **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = [('partner_id', '=', user.partner_id.id)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'date_desc': {'label': _('Oldest'), 'order': 'create_date asc'},
        }
        searchbar_inputs = {
            'desc': {'input': 'desc', 'label': _('Description')}
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = []
        # archive_groups = self._get_archive_groups('ebs_mod.contact.payment', domain)
        # if date_begin and date_end:
        #     domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in == 'desc':
                search_domain = OR([search_domain, [('desc', 'ilike', search)]])
            domain += search_domain

        # pager
        payment_count = request.env['ebs_mod.contact.payment'].search_count(domain)
        pager = portal_pager(
            url="/my/payments",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=payment_count,
            page=page,
            step=self._items_per_page
        )

        payments = request.env['ebs_mod.contact.payment'].search(domain, order=order, limit=self._items_per_page,
                                                                 offset=pager['offset'])
        request.session['my_payments_history'] = payments.ids[:100]
        values.update({
            'date': date_begin,
            'payments': payments,
            'page_name': 'payment',
            'default_url': '/my/payments',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render("ebs_qsheild_mod.portal_contact_payment", values)

    @http.route(['/my/payments/insert_form'], type='http', auth='user', website=True)
    def contact_payment_insert_form(self):

        values = {
            'page_name': 'payment_insert',
            'currency': request.env.company.currency_id
        }

        return request.render("ebs_qsheild_mod.portal_contact_payment_form", values)

    @http.route(['/my/payments/insert'], type='http', auth='user', website=True)
    def contact_payment_insert(self):

        request.env['ebs_mod.contact.payment'].create({
            'partner_id': request.env.user.partner_id.id,
            'amount': float(request.params['amount']),
            'currency_id': int(request.params['currency']),
            'desc': request.params['desc'],
        })
        return self.contact_payment_insert_form()


class CustomerPortal(CustomerPortal):
    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        values['ticket_count'] = request.env['helpdesk.ticket'].search_count(
            [('partner_id', '=', request.env.user.partner_id.id)])
        if values.get('sales_user', False):
            values['title'] = _("Salesperson")
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=True)
    def my_helpdesk_tickets(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content',
                            **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = [('partner_id', '=', user.partner_id.id)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'id': {'input': 'id', 'label': _('Search ID')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        # archive groups - Default Group By 'create_date'
        archive_groups = self._get_archive_groups('helpdesk.ticket', domain)
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            domain += search_domain

        # pager
        tickets_count = request.env['helpdesk.ticket'].search_count(domain)
        pager = portal_pager(
            url="/my/tickets",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby},
            total=tickets_count,
            page=page,
            step=self._items_per_page
        )

        tickets = request.env['helpdesk.ticket'].search(domain, order=order, limit=self._items_per_page,
                                                        offset=pager['offset'])
        request.session['my_tickets_history'] = tickets.ids[:100]

        values.update({
            'date': date_begin,
            'tickets': tickets,
            'page_name': 'ticket',
            'default_url': '/my/tickets',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'search_in': search_in,
            'search': search,
        })
        return request.render("helpdesk.portal_helpdesk_ticket", values)
