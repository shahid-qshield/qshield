# -*- coding: utf-8 -*-

{
    'name': 'Hide archive action',
    'description': 'Hide archive action',
    'version': '0.0.1',
    'summary': 'Hide archive action',
    'license': 'OPL-1',
    'author': 'TechUltra Solutions Pvt. Ltd.',
    'website': 'https://www.techultrasolutions.com/',
    'images': [],
    'category': 'uncategorized',
    'description': """Hide archive action""",
    'depends': ['ebs_qsheild_mod'],
    'data': [
        'wizard/confirmation_archive_wizard.xml',
        'views/templates.xml',
        'views/service_request_view.xml',

    ],
    'auto_install': False,
}

# depends
# security_rules for the assess group
# hr_appraisal for view and the group override
