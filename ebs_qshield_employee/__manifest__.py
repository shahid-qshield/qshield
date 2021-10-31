# -*- coding: utf-8 -*-
{
    'name': "QShield Module",
    'summary': """
        This module contains custom modifications for QSshield Employee Module
        """,
    'description': """
       This module contains custom modifications for QSshield Employee Module
    """,
    'author': "Maria L Soliman",
    'website': "http://www.ever-bs.com/",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'contacts', 'hr', 'hr_contract', 'documents', 'helpdesk', 'documents_hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/contacts_view_custom.xml',
        'views/employee_view_custom.xml',
        'views/contracts_view_custom.xml',
        'reports/employee_information_form.xml',
    ],
}
