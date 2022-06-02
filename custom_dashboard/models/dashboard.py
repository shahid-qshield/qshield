# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
import os
import xlrd


class ServiceRequest(models.Model):
    _inherit = 'ebs_mod.service.request'

    is_exceptional = fields.Boolean()
    is_one_time_transaction = fields.Boolean()
    is_overdue = fields.Boolean()
    is_governmental_fees = fields.Boolean('Governmental Fees')
    governmental_fees = fields.Integer('Governmental Fees Amount')
    is_out_of_scope = fields.Boolean("Is Out of Scope")

    @api.model
    def get_request(self, args=""):
        request_dict = {}
        status_dict = {
            'draft': 'Draft',
            'new': 'New',
            'progress': 'In Progress',
            'hold': 'On Hold',
            'pending': 'Pending from Gov',
            'pending_payment': 'Pending Payment',
            'escalated': 'Escalated',
            'incomplete': 'Incomplete',
            'escalated_incomplete': 'Escalated Incomplete',
            'escalated_progress': 'Escalated In Progress',
            'escalated_complete': 'Escalated Completed',
            'complete': 'Completed',
            'reject': 'Rejected',
            'cancel': 'Canceled'
        }
        for key in status_dict:
            if args:
                domain = [('status', '=', key), ('date', '>=', args.get('date_from')),
                          ('date', '<=', args.get('date_to'))]
            else:
                domain = [('status', '=', key)]

            no_of_requests = self.env['ebs_mod.service.request'].search_count(domain)
            request_dict[key] = no_of_requests

        progress_overdue = self.env['ebs_mod.service.request'].search(
            [('status', '=', 'progress'), ('date', '>=', args.get('date_from')), ('date', '<=', args.get('date_to'))])
        for each in progress_overdue:
            if each.progress_date:
                today = date.today()
                if each.progress_date + timedelta(days=each.exceeded_days) < today:
                    each.with_context(call_from_dashboard=True).write({'is_overdue': True})
        overdue = self.env['ebs_mod.service.request'].search_count([('is_overdue', '=', True),
                                                                    ('date', '>=', args.get('date_from')),
                                                                    ('date', '<=', args.get('date_to'))])
        progress_normal = self.env['ebs_mod.service.request'].search_count([('status', '=', 'progress'),
                                                                            ('is_exceptional', '=', False),
                                                                            ('date', '>=', args.get('date_from')),
                                                                            ('date', '<=', args.get('date_to'))])
        progress_exceptional = self.env['ebs_mod.service.request'].search_count([('is_exceptional', '=', True),
                                                                                 ('date', '>=', args.get('date_from')),
                                                                                 ('date', '<=', args.get('date_to'))
                                                                                 ])
        progress_out_of_scope = self.env['ebs_mod.service.request'].search_count([('is_out_of_scope', '=', True),
                                                                                  ('date', '>=', args.get('date_from')),
                                                                                  ('date', '<=', args.get('date_to'))])
        request_miscellaneous = self.env['ebs_mod.service.request'].search_count([('is_miscellaneous', '=', True),
                                                                                  ('date', '>=', args.get('date_from')),
                                                                                  ('date', '<=', args.get('date_to'))
                                                                                  ])
        request_one_time_transaction = self.env['ebs_mod.service.request'].search_count(
            [('is_one_time_transaction', '=', True)])

        request_dict['overdue'] = overdue
        request_dict['progress_normal'] = progress_normal
        request_dict['progress_out_of_scope'] = progress_out_of_scope
        request_dict['progress_exceptional'] = progress_exceptional
        request_dict['request_miscellaneous'] = request_miscellaneous
        request_dict['request_one_time_transaction'] = request_one_time_transaction
        print(request_dict)
        return request_dict


class ServiceTypeWorkflow(models.Model):
    _inherit = "ebs_mod.service.type.workflow"

    requires_driver = fields.Boolean(required=False, default=False)


class ServiceRequestWorkFlow(models.Model):
    _inherit = 'ebs_mod.service.request.workflow'

    def _domain_drivers(self):
        job_ids = self.env['hr.job'].search([('name', 'in', ['PRO', 'Driver'])])
        return [('job_id', 'in', job_ids.ids)] if job_ids else []

    requires_driver = fields.Boolean(required=False,
                                     related="workflow_id.requires_driver",
                                     store=True, readonly=True)
    driver = fields.Many2one('hr.employee', string='Driver', domain=_domain_drivers)
    time_slot_type = fields.Selection([('7', '7:00 - 7:59 AM'),
                                       ('8', '8:00 - 8:59 AM'),
                                       ('9', '9:00 - 9:59 AM'),
                                       ('10', '10:00 - 10:59 AM'),
                                       ('11', '11:00 - 11:59 AM'),
                                       ('12', '12:00 - 12:59 PM'),
                                       ('1', '1:00 - 1:59 PM'),
                                       ('2', '2:00 - 2:59 PM'),
                                       ('3', '3:00 - 3:59 PM'),
                                       ('4', '4:00 - 4:59 PM'),
                                       ('5', '5:00 - 5:59 PM'),
                                       ('6', '6:00 - 6:59 PM')])
    delivery_date = fields.Date()
    destination_id = fields.Many2one('ebs_mod.service.destination', 'Destination Name')

    @api.onchange('driver', 'destination_id', 'delivery_date', 'time_slot_type')
    @api.depends('driver', 'destination_id', 'delivery_date', 'time_slot_type')
    def check_driver(self):
        if self.driver and self.destination_id and self.delivery_date and self.time_slot_type:
            check_date_slot = self.env['ebs_mod.service.request.workflow'].search([('driver', '=', self.driver.id),
                                                                                   ('delivery_date', '=',
                                                                                    self.delivery_date),
                                                                                   ('destination_id', '!=',
                                                                                    self.destination_id.id),
                                                                                   ('time_slot_type', '=',
                                                                                    self.time_slot_type)])
            if check_date_slot:
                my_error_msg = "The driver {} is assigned to another task on {} at {}. Destinations: ".format(
                    self.driver.name, self.delivery_date, self.time_slot_type)
                for each_destination in check_date_slot:
                    my_error_msg += ' {},'.format(each_destination.destination_id.name)
                title = "Warning"
                warning = {
                    'title': title,
                    'message': my_error_msg,
                }
                return {'warning': warning}
        else:
            return False

    @api.model
    def get_request(self, args=""):
        request_list = []
        employees = self.env['res.users'].search([])
        for each_employee in employees:
            domain = []
            if args:
                if args.get('date_from') and args.get('date_to'):
                    year_from, month_from, day_from = map(int, args.get('date_from').split('-'))
                    year_to, month_to, day_to = map(int, args.get('date_to').split('-'))
                    date_from = datetime(year_from, month_from, day_from, 0, 0, 0)
                    date_to = datetime(year_to, month_to, day_to, 0, 0, 0)
                    domain.extend(
                        [('due_date', '>=', date_from), ('due_date', '<=', date_to), ('status', '=', 'progress'),
                         ('assign_to', '=', each_employee.id)])
            else:
                domain.extend([('status', '=', 'progress'), ('assign_to', '=', each_employee.id)])
            no_of_requests = self.env['ebs_mod.service.request.workflow'].search_count(domain)
            if no_of_requests:
                request_dict = {
                    'employee_id': each_employee.id,
                    'employee_name': each_employee.name,
                    'employee_image': each_employee.image_1920,
                    'progress': no_of_requests
                }
                request_list.append(request_dict.copy())

        def get_progress(elem):
            return elem.get('progress')

        request_list.sort(key=get_progress, reverse=True)
        return request_list

    # @api.model
    # def get_request(self, args=""):
    #     request_list = []
    #     if args:
    #         domain = [('date', '>=', args.get('date_from')), ('date', '<=', args.get('date_to'))]
    #     else:
    #         domain = []
    #     employees = self.env['res.users'].search(domain)
    #     for each_employee in employees:
    #         domain = [('status', '=', 'progress'), ('assign_to', '=', each_employee.id)]
    #         no_of_requests = self.env['ebs_mod.service.request.workflow'].search_count(domain)
    #         if no_of_requests:
    #             request_dict = {
    #                 'employee_id': each_employee.id,
    #                 'employee_name': each_employee.name,
    #                 'employee_image': each_employee.image_1920,
    #                 'progress': no_of_requests
    #             }
    #             request_list.append(request_dict.copy())
    #
    #     def get_progress(elem):
    #         return elem.get('progress')
    #
    #     request_list.sort(key=get_progress, reverse=True)
    #     return request_list

    @api.model
    def get_driver(self, args=""):
        request_list = []
        job_ids = self.env['hr.job'].search([('name', 'in', ['PRO', 'Driver'])])
        drivers = self.env['hr.employee'].search([('job_id', 'in', job_ids.ids)])
        for each_driver in drivers:
            today = datetime.today()
            if args:
                domain = [('status', '=', 'progress'), ('driver', '=', each_driver.id),
                          ('delivery_date', '=', args.get('date_day'))]
            else:
                domain = [('status', '=', 'progress'), ('driver', '=', each_driver.id),
                          ('delivery_date', '=', today)]
            destinations = self.env['ebs_mod.service.request.workflow'].search(domain)
            if destinations:
                request_dict = {
                    'driver_id': each_driver.id,
                    'driver_name': each_driver.name,
                    'destination': []
                }
                for each_destination in destinations:
                    request_dict['destination'].append({'destination': each_destination.destination_id.name,
                                                        'slot': each_destination.time_slot_type})
                request_list.append(request_dict.copy())
        return request_list


class ServiceTypes(models.Model):
    _inherit = 'ebs_mod.service.types'

    consolidation_id = fields.Many2one('ebs_mod.service.type.consolidation', 'Consolidation Name', store=True)
    variant_id = fields.Many2one('ebs_mod.service.type.variants', 'Variant Name', store=True)


class ServiceDestination(models.Model):
    _name = 'ebs_mod.service.destination'

    name = fields.Char('Destination Name')


class ServiceTypeConsolidation(models.Model):
    _name = 'ebs_mod.service.type.consolidation'

    name = fields.Char('Consolidation Name')
    service_type = fields.One2many('ebs_mod.service.types', 'consolidation_id')
    service_type_variant_ids = fields.One2many('ebs_mod.service.type.variants', 'consolidation_id')

    def import_service_type_consolidation(self):
        print('----------------------------')
        file_path = os.path.dirname(os.path.dirname(__file__)) + '/demo/service_type_consolidation.xls'
        with open(file_path, 'rb') as f:
            try:
                file_data = f.read()
                workbook = xlrd.open_workbook(file_contents=file_data)
                worksheet = workbook.sheet_by_index(1)
                first_row = []
                for col in range(worksheet.ncols):
                    first_row.append(worksheet.cell_value(0, col))
                data = []
                for row in range(1, worksheet.nrows):
                    elm = {}
                    for col in range(worksheet.ncols):
                        if worksheet.cell_value(row, col) != '' and worksheet.cell_value(row, col) != 'NA':
                            elm[first_row[col]] = worksheet.cell_value(row, col)
                        else:
                            elm[first_row[col]] = False
                    data.append(elm)
                for record in data:
                    if record.get('Code') == 'WV':
                        print('---------------------------')
                    if record.get('Code'):
                        service_type = self.env['ebs_mod.service.types'].sudo().search(
                            [('code', '=', record.get('Code'))], limit=1)
                        if service_type and record.get('Original Products'):
                            self.env['ebs_mod.service.types'].sudo().write({'name': record.get('Original Products')})
                        if not service_type:
                            service_type = self.env['ebs_mod.service.types'].sudo().create({
                                'name': record.get('Original Products') if record.get(
                                    'Original Products') else record.get('Variants'),
                                'code': record.get('Code')
                            })
                    if record.get('Variants'):
                        service_type_variant = self.env['ebs_mod.service.type.variants'].sudo().search(
                            [('name', '=', record.get('Variants'))])
                        if service_type_variant:
                            self.env['ebs_mod.service.type.variants'].sudo().write({'name': record.get('Variants')})
                        else:
                            service_type_variant = self.env['ebs_mod.service.type.variants'].sudo().create({
                                'name': record.get('Variants')
                            })
                        if service_type and service_type.id not in service_type_variant.service_type.ids:
                            service_type_variant.sudo().write({
                                'service_type': [(4, service_type.id)]
                            })
                    if record.get('Grouped Services'):
                        service_type_consolidation = self.env['ebs_mod.service.type.consolidation'].sudo().search(
                            [('name', '=', record.get('Grouped Services'))])
                        if service_type_consolidation:
                            self.env['ebs_mod.service.type.consolidation'].sudo().write(
                                {'name': record.get('Grouped Services')})
                        else:
                            service_type_consolidation = self.env['ebs_mod.service.type.consolidation'].sudo().create({
                                'name': record.get('Grouped Services')
                            })
                        if service_type_variant and service_type_variant.id not in \
                                service_type_consolidation.service_type_variant_ids.ids:
                            service_type_consolidation.sudo().write(
                                {'service_type_variant_ids': [(4, service_type_variant.id)]})

            except Exception as e:
                print('Something Wrong', e)

    @api.model
    def get_request(self):
        request_list = []
        consolidated = self.env['ebs_mod.service.type.consolidation'].search([])
        for each_consolidated in consolidated:
            domain = [('consolidation_id', '=', each_consolidated.id)]
            service_types = self.env['ebs_mod.service.types'].search(domain)
            no_of_all = 0
            for each_service_type in service_types:
                # print(each_service_type)
                domain = [('status', '=', 'progress'), ('service_type_id', '=', each_service_type.id)]
                no_of_inprogress = self.env['ebs_mod.service.request'].search_count(domain)
                no_of_all += no_of_inprogress
            if no_of_all:
                request_dict = {
                    'consolidated_service_id': each_consolidated.id,
                    'consolidated_service_name': each_consolidated.name,
                    'count': no_of_all
                }
                request_list.append(request_dict.copy())
        return request_list


class ServiceTypeVariants(models.Model):
    _name = 'ebs_mod.service.type.variants'

    consolidation_id = fields.Many2one('ebs_mod.service.type.consolidation')
    name = fields.Char(string="Variant Name")
    service_type = fields.One2many('ebs_mod.service.types', 'variant_id')
