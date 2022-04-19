
{
    "name": "Purchase - Custom",
    "summary": "Purchase - Custom",
    "version": "12.0.1",
    'category': 'Purchase',
	"description": """
		 Purchase Custom	 
		 
    """,
	
    "author": "Oodu Implementers Private Limited",
    "website": "https://www.odooimplementers.com",
    "license": "LGPL-3",
    "installable": True,
    "depends": ['base', 'purchase', 'stock', 'purchase_stock', 
    ],
    "data": [
            'security/ir.model.access.csv',      
            'wizard/wizard_views.xml',      
            # 'view/purchase.xml',
            # 'view/configuration.xml',
            # 'view/purchase_tracking.xml',
            # 'view/gatepass.xml'
    ],
    
    'installable': True,
    'auto_install': True,    
    
       
}

