# -*- coding: utf-8 -*-
{
    'name': "Q shield Access right",

    'summary': """
        this module id user for the add groups on button and menu""",

    'description': """
        this module id user for the add groups on button and menu
    """,

    'author': "Tech Ultra Solutions",
    'website': "http://www.techultrasolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['ebs_qshield_employee', 'qshield_letter_request','matco_loan_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/templates.xml',
        'views/menus.xml',
    ],
}
