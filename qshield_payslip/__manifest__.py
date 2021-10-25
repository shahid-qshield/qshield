
{
    'name': 'Qsheild Payslip',
    'version': '13.0',
    'summary': 'Payslip',
    'description': """
        Qsheild Payslip
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "",
    'company': '',
    'maintainer': '',
    'website': "",
    'depends': ['base', 'hr', 'ebs_qshield_employee'],
    'data': [
        'views/payslip_view.xml',
        'reports/payslip_report.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
