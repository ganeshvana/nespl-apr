# -*- coding: utf-8 -*-

from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute("ALTER TABLE account_move ADD COLUMN company_shipping_id INT")
    cr.execute("UPDATE account_move SET company_shipping_id = dispatch_partner_id")
    cr.execute("""
        UPDATE ir_ui_view
           SET active='f'
         WHERE id IN (SELECT res_id FROM ir_model_data WHERE name=%s AND module=%s)
    """, ['invoice_form_inherit_l10n_in', 'l10n_in_extend'])

    cr.execute("""
            SELECT count(1)
              FROM ir_module_module
             WHERE name = 'l10n_in_einvoice'
               AND state in ('installed', 'to install', 'to upgrade')
    """)
    if cr.fetchone()[0]:
        cr.execute("UPDATE ir_module_module SET state='uninstalled' WHERE name=%s", ('l10n_in_einvoice',))
        cr.execute("CREATE TABLE l10n_in_einvoice_transaction_copy AS TABLE l10n_in_einvoice_transaction")
        cr.execute("CREATE TABLE l10n_in_einvoice_service_copy AS TABLE l10n_in_einvoice_service")
