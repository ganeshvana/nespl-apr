# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from . import models
from . import wizard

from odoo import api, SUPERUSER_ID


def post_init_create_edi_records(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """
            SELECT 1
              FROM information_schema.tables
             WHERE table_name = 'l10n_in_einvoice_transaction_copy'
               AND table_type = 'BASE TABLE'
    """)
    if cr.fetchone() is not None:
        edi_format_id = env.ref('l10n_in_edi_custom.edi_in_einvoice_json_1_03').id
        cr.execute("select move.name ,t.move_id, t.response_json, t.cancel_response_json, t.status from l10n_in_einvoice_transaction_copy as t join account_move as move on move.id = t.move_id")
        for trn in cr.dictfetchall():
            if not env['account.edi.document'].search([
                ('move_id','=',trn.get('move_id')),
                ('edi_format_id','=',edi_format_id),
            ]):
                attachment_id = env["ir.attachment"].create({
                    "name": "%s%s.josn"%(trn.get('name'),trn.get('status')),
                    "raw": (trn.get('status') == 'cancel' and trn.get('cancel_response_json') or trn.get('response_json')).encode(),
                    "res_model": "account.move",
                    "res_id": trn.get('move_id'),
                    "mimetype": "application/json",
                })
                env['account.edi.document'].create({
                    'move_id': trn.get('move_id'),
                    'edi_format_id': edi_format_id,
                    'attachment_id': attachment_id.id,
                    'state': trn.get('status') == 'cancel' and 'cancelled' or 'sent',
                })

    cr.execute(
        """
            SELECT 1
              FROM information_schema.tables
             WHERE table_name = 'l10n_in_einvoice_service_copy'
               AND table_type = 'BASE TABLE'
    """)
    if cr.fetchone() is not None:
        cr.execute("""
            UPDATE res_company
               SET l10n_in_edi_username=ein_s.gstn_username,
                   l10n_in_edi_password=ein_s.gstn_password
              FROM l10n_in_einvoice_service_copy ein_s
             WHERE ein_s.partner_id=res_company.partner_id
               AND ein_s.token IS NOT NULL
        """)
        cr.execute("""
            INSERT INTO l10n_in_edi_web_service (company_id, token, token_validity)
            SELECT c.id, sc.token, sc.token_validity
              FROM res_company c
              JOIN l10n_in_einvoice_service_copy sc on sc.partner_id = c.partner_id
               AND sc.token IS NOT NULL
        """)
        cr.execute("""
            INSERT INTO account_edi_format_account_journal_rel (account_journal_id,account_edi_format_id)
            SELECT am.journal_id,edif.id
              FROM account_edi_document doc
              JOIN account_edi_format edif on edif.id = doc.edi_format_id
              JOIN account_move am on am.id = doc.move_id
             WHERE edif.code='in_einvoice_1_03'
          GROUP BY am.journal_id, edif.id
                ON CONFLICT DO NOTHING
            """)
