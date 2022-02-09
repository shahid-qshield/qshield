# -*- coding: utf-8 -*-
{
    'name': "qshield_letter_request",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/ebs_hr_letter_request_view.xml',
        'views/hr_employee_custom.xml',
        'data/ir_sequence_data.xml',
        'report/form_header.xml',
        'report/report.xml',
        'report/liquor_permit.xml',
        'report/noc_visa.xml',
        'report/termination_letter.xml',
        'report/salary_certificate.xml',
        'report/bank_salary_certificate.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
