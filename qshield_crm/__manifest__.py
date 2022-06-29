# -*- coding: utf-8 -*-
{
    'name': "Qshield CRM",

    'summary': """Custom CRM""",

    'description': """
        Customization in CRM
    """,

    'author': "Tech Ultra Solutions",
    'website': "http://www.techultrasolutions.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0.4',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale_crm', 'ebs_qsheild_mod', 'sale_management', 'custom_dashboard'],

    # always loaded
    'data': [
        'security/qshiled_security_groups.xml',
        'security/ir.model.access.csv',
        'report/qshied_proposal_report.xml',
        'report/quotation_report_template_inherit.xml',
        'report/qshield_expense_invoice_report.xml',
        'report/qshield_monthly_invoice.xml',
        'data/ir_mail_activity.xml',
        'data/ir_cron_create_invoice.xml',
        'wizards/refuse_quotation_view.xml',
        'wizards/create_multiple_invoice.xml',
        'views/generate_sale_order_line_view.xml',
        'views/crm_lead_view.xml',
        'views/sale_order_view.xml',
        'views/account_move_views.xml',
        'views/sale_order_approver_settings_view.xml',
        'views/ebs_mod_service_request_view.xml',
        'views/sale_order_template_inherit.xml',
        'views/res_partner_view.xml',
    ],
}
