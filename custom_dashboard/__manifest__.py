# -*- coding: utf-8 -*-
{
    'name': "Custom Dashboard",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Ever Business Solutions",
    'website': "https://www.everbsgroup.com/",
    'category': 'Uncategorized',
    'version': '0.3',
    'depends': ['base', 'ebs_qsheild_mod'],
    'qweb': ["static/src/xml/dashboard.xml"],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_views.xml',
        'views/dashboard_view.xml',
    ],
    'images': ['static/description/dashboard_icon.png'],
    'installable': True,
    'application': True,
}
