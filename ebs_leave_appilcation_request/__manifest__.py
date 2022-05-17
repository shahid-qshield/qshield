# -*- coding: utf-8 -*-
{
    'name': "ebs_leave_appilcation_request",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.2',
    'depends': ['base', 'hr', 'hr_holidays', 'hr_contract', 'matco_loan_management'],
    'data': [
        'data/ir_cron_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/report.xml',
        'report/leave_application_form.xml',
        'views/hr_contract_custom.xml',
        'views/world_airport.xml',
        'views/hr_leave_custom.xml',
    ],
}
