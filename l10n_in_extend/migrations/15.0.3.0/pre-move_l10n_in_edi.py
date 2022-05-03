# -*- coding: utf-8 -*-

from odoo import api
from odoo import SUPERUSER_ID

def migrate(cr, version):
    cr.execute("""
            SELECT count(1)
              FROM ir_module_module
             WHERE name = 'l10n_in_edi'
               AND state in ('installed', 'to install', 'to upgrade')
    """)
    if cr.fetchone()[0]:
        env = api.Environment(cr, SUPERUSER_ID, {})
        cr.execute("UPDATE ir_module_module SET state='uninstalled' WHERE name=%s", ('l10n_in_edi',))
        cr.execute("UPDATE ir_module_module SET state='to upgrade' WHERE name=%s", ('l10n_in_edi_custom',))
        #_update_view_key(cr, 'l10n_in_edi', new)
        cr.execute("UPDATE ir_model_data SET module=%s WHERE module=%s", ('l10n_in_edi_custom', 'l10n_in_edi'))
        cr.execute("UPDATE ir_translation SET module=%s WHERE module=%s", ['l10n_in_edi_custom', 'l10n_in_edi'])
    cr.execute("UPDATE ir_module_module_dependency SET name=%s WHERE name=%s", ('l10n_in_edi_custom', 'l10n_in_edi'))
