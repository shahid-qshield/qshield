# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ServiceRequest(models.Model):
    _inherit = 'ebs_mod.service.request'

    @api.model
    def get_request(self, date_from='', date_to=''):
        if date_to and date_from:
            pass
        else:
            request_dict = {}
            status_dict = {
                'draft': 'Draft',
                'progress': 'In Progress',
                'hold': 'On Hold',
                'complete': 'Completed',
                'reject': 'Rejected',
                'cancel': 'Canceled'
            }
            for key in status_dict:
                domain = [('status', '=', key)]
                no_of_requests = self.env['ebs_mod.service.request'].search_count(domain)
                request_dict[key] = no_of_requests
        return request_dict


class ServiceRequestWorkFlow(models.Model):
    _inherit = 'ebs_mod.service.request.workflow'

    @api.model
    def get_request(self, date_from='', date_to=''):
        request_list = []
        if date_to and date_from:
            pass
        else:
            employees = self.env['res.users'].search([])
            for each_employee in employees:
                domain = [('status', '=', 'progress'), ('assign_to', '=', each_employee.id)]
                no_of_requests = self.env['ebs_mod.service.request.workflow'].search_count(domain)
                request_dict = {
                    'employee_id': each_employee.id,
                    'employee_name': each_employee.name,
                    'progress': no_of_requests
                }
                request_list.append(request_dict.copy())
        return request_list
