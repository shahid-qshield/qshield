# -*- coding: utf-8 -*-
{
    'name': "custom_dashboard",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'ebs_qsheild_mod'],
    'qweb': ["static/src/xml/dashboard.xml"],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_views.xml',
        # 'views/templates.xml',
        'views/dashboard_view.xml',
    ],
}
