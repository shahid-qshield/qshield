
{
    'name': 'Matco Loan Management',
    'version': '13.0',
    'summary': 'Manage Loan Requests',
    'description': """
        Helps you to manage Loan Requests of your company's staff.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "",
    'company': '',
    'maintainer': '',
    'website': "",
    'depends': ['base', 'hr', 'hr_contract'],
    'data': [
        'data/salary_rule_loan.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_loan_seq.xml',
        'views/hr_loan.xml',
        'views/hr_payroll.xml',
        'reports/hr_loan_report.xml',
    ],
    'demo': [],    
    'installable': True,
    'auto_install': False,
    'application': False,
}
