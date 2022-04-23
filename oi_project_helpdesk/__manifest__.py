# -*- coding: utf-8 -*-
{
    'name': 'Custom Project-Helpdesk',
    'version': '0.1',
    'category': 'Facility',
    'license': 'OPL-1',
    'author': 'Oodu implementers Pvt. Ltd.',
    'currency': 'EUR',
    'summary': 'Custom Project-Helpdesk',
    'description': """
    Custom Project-Helpdesk
""",
    'depends': ['base', 'mail', 'project', 'helpdesk', 'hr_expense', 'crm', 'survey', 'hr'],
    'data': [
        'security/security.xml',
        # 'security/ir.model.access.csv',
        # 'wizard/cancel_purchase.xml',
        # 'report/letter_print.xml',
        'views/project.xml',
        'views/helpdesk.xml',
        'views/expense.xml',
        'views/employee.xml',
        'views/crm.xml',
        'views/sequence.xml',
    ],
    'installable': True,
    'application': True,
}
