
{
    "name": "Auto Lot",
    "summary": "Auto Lot",
    "version": "12.0.1",
    'category': 'Inventory',
    "website": "",
	"description": """
		 	 
		 
    """,
	
    "author": "",
    "license": "LGPL-3",
    "installable": True,
    "depends": ['base', 'stock'
    ],
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/wizard_invoice.xml',
        'view/stock_move.xml',
    ],
    
    'installable': True,
    'auto_install': True,    
       
}

