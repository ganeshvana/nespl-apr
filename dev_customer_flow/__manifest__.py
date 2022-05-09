# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Devintelle Software Solutions (<http://devintellecs.com>).
#
##############################################################################

{
    'name': 'Customer/Supplier Approval Workflow',
    'version': '15.0.1.0',
    'category': 'Generic Modules/Sales Management',
    'description': """
        Customer/Supplier Approval Workflow- Validation Process
        
        Customer/Supplier Approval Workflow validation Process When any new customer or supplier created in odoo
        Only access rights user can validate newly Customer/Supplier work flow
        Generate unique number for customer and supplier approval to easy identification.
        Approval user can approve or confirm Customer/Supplier work flow 
        Easy view to see customer/supplier approval status on kanban view 
        Quick filter to check status of customer/supplier approval
        Only approval customer will be listed on sale order, delivery order, customer invoice into customer drop down
        Only approval supplier will be listed on purchase order, shipment, vendor bill into vendor drop down
        Only approval vendor will be listed product supplier list
        
    Customer flow 
    Odoo customer flow 
    Customer validation process 
    Odoo customer validation process 
    Manage customer validation process 
    Odoo manage customer validation process 
    For Helping You validate the customer in odoo.
    Odoo For Helping You validate the customer in odoo
    Validation flow on customer screen.
    Odoo Validation flow on customer screen.
    Validate Customer will show on sale order,purchase,invoice and delivery screen.
    Odoo Validate Customer will show on sale order,purchase,invoice and delivery screen.
    Customer validation 
    Odoo customer validation 
    Customer validate button access right 
    Odoo customer validate button access right 
    Customer form 
    Odoo customer form 
    Approval button access right 
    Odoo approval button access right 
    Customer sale order form 
    Odoo customer sale order form 
    Customer approval process 
    Odoo customer approval process 
    supplier flow 
    Odoo supplier flow 
    supplier validation process 
    Odoo supplier validation process 
    Manage supplier validation process 
    Odoo manage supplier validation process 
    For Helping You validate the supplier in odoo.
    Odoo For Helping You validate the supplier in odoo
    Validation flow on supplier screen.
    Odoo Validation flow on supplier screen.
    Validate supplier will show on sale order,purchase,invoice and delivery screen.
    Odoo Validate supplier will show on sale order,purchase,invoice and delivery screen.
    supplier validation 
    Odoo supplier validation 
    supplier validate button access right 
    Odoo supplier validate button access right 
    supplier form 
    Odoo supplier form 
    Approval button access right 
    Odoo approval button access right 
    supplier sale order form 
    Odoo supplier sale order form 
    supplier approval process 
    Odoo supplier approval process         
        
    """,
    'summary':'odoo app will manage Customer/Supplier Approval Workflow validation process',
    'depends': ['sale','stock','account','purchase',],
    'data': [
        'security/dev_customer_access.xml',
        'data/res_partner_seq_view.xml',
        'views/res_customer_view.xml',
        'views/sale_order_view.xml',
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    #author and support Details
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':25.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
