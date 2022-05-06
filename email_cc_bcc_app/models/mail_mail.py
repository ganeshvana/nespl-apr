# -*- coding: utf-8 -*-


import base64
import psycopg2
import logging
import smtplib
import re
import threading

from email.utils import formataddr
from odoo import _, api, exceptions, fields, models, tools, registry, SUPERUSER_ID, Command
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo.tools import pycompat, ustr
from odoo.tools.misc import clean_context, split_every
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)



class MailMail(models.Model):
	_inherit = 'mail.mail'

	notification = fields.Boolean("Notify")
	recipient_cc_ids = fields.Many2many(
		'res.partner', 'mail_mail_cc_res_partner_rel',
		'mail_mail_id', 'partner_id', 'CC (Partners)')

	recipient_bcc_ids = fields.Many2many(
		'res.partner', 'mail_mail_bcc_res_partner_rel',
		'mail_mail_id', 'partner_id', 'BCC (Partners)')


	def _send(self, auto_commit=False, raise_exception=False, smtp_session=None):
		IrMailServer = self.env['ir.mail_server']
		IrAttachment = self.env['ir.attachment']
		for mail_id in self.ids:
			success_pids = []
			failure_type = None
			processing_pid = None
			mail = None
			try:
				mail = self.browse(mail_id)
				if mail.state != 'outgoing':
					if mail.state != 'exception' and mail.auto_delete:
						mail.sudo().unlink()
					continue

				# remove attachments if user send the link with the access_token
				body = mail.body_html or ''
				attachments = mail.attachment_ids
				for link in re.findall(r'/web/(?:content|image)/([0-9]+)', body):
					attachments = attachments - IrAttachment.browse(int(link))

				# load attachment binary data with a separate read(), as prefetching all
				# `datas` (binary field) could bloat the browse cache, triggerring
				# soft/hard mem limits with temporary data.
				attachments = [(a['name'], base64.b64decode(a['datas']), a['mimetype'])
							   for a in attachments.sudo().read(['name', 'datas', 'mimetype']) if a['datas'] is not False]

				# specific behavior to customize the send email for notified partners
				email_list = []
				if mail.email_to:
					email_list.append(mail._send_prepare_values())
				for partner in mail.recipient_ids:
					values = mail._send_prepare_values(partner=partner)
					values['partner_id'] = partner
					email_list.append(values)

				# Custom Code
				if mail.cc_visible:
					email_cc_list = []
					for partner_cc in mail.recipient_cc_ids:
						email_to = formataddr((partner_cc.name or 'False', partner_cc.email or 'False'))
						email_cc_list.append(email_to)
					# Convert Email List To String For BCC & CC
					email_cc_string = ','.join(email_cc_list)

				else:
					email_cc_string = ''

				if mail.bcc_visible:
					email_bcc_list = []
					for partner_bcc in mail.recipient_bcc_ids:
						email_to = formataddr((partner_bcc.name or 'False', partner_bcc.email or 'False'))
						email_bcc_list.append(email_to)
					# Convert Email List To String For BCC & CC
					email_bcc_string = ','.join(email_bcc_list)
				else:
					email_bcc_string = ''

				# headers
				headers = {}
				ICP = self.env['ir.config_parameter'].sudo()
				bounce_alias = ICP.get_param("mail.bounce.alias")
				catchall_domain = ICP.get_param("mail.catchall.domain")
				if bounce_alias and catchall_domain:
					headers['Return-Path'] = '%s@%s' % (bounce_alias, catchall_domain)
				if mail.headers:
					try:
						headers.update(ast.literal_eval(mail.headers))
					except Exception:
						pass

				# Writing on the mail object may fail (e.g. lock on user) which
				# would trigger a rollback *after* actually sending the email.
				# To avoid sending twice the same email, provoke the failure earlier
				mail.write({
					'state': 'exception',
					'failure_reason': _('Error without exception. Probably due do sending an email without computed recipients.'),
				})
				# Update notification in a transient exception state to avoid concurrent
				# update in case an email bounces while sending all emails related to current
				# mail record.
				notifs = self.env['mail.notification'].search([
					('notification_type', '=', 'email'),
					('mail_mail_id', 'in', mail.ids),
					('notification_status', 'not in', ('sent', 'canceled'))
				])
				if notifs:
					notif_msg = _('Error without exception. Probably due do concurrent access update of notification records. Please see with an administrator.')
					notifs.sudo().write({
						'notification_status': 'exception',
						'failure_type': 'unknown',
						'failure_reason': notif_msg,
					})
					# `test_mail_bounce_during_send`, force immediate update to obtain the lock.
					# see rev. 56596e5240ef920df14d99087451ce6f06ac6d36
					notifs.flush(fnames=['notification_status', 'failure_type', 'failure_reason'], records=notifs)

				# build an RFC2822 email.message.Message object and send it without queuing
				res = None
				# TDE note: could be great to pre-detect missing to/cc and skip sending it
				# to go directly to failed state update
				for email in email_list:
					msg = IrMailServer.build_email(
						email_from=mail.email_from,
						email_to=email.get('email_to'),
						subject=mail.subject,
						body=email.get('body'),
						body_alternative=email.get('body_alternative'),
						email_cc=tools.email_split(email_cc_string),
						email_bcc=tools.email_split(email_bcc_string),
						reply_to=mail.reply_to,
						attachments=attachments,
						message_id=mail.message_id,
						references=mail.references,
						object_id=mail.res_id and ('%s-%s' % (mail.res_id, mail.model)),
						subtype='html',
						subtype_alternative='plain',
						headers=headers)
					processing_pid = email.pop("partner_id", None)
					try:
						res = IrMailServer.send_email(
							msg, mail_server_id=mail.mail_server_id.id, smtp_session=smtp_session)
						if processing_pid:
							success_pids.append(processing_pid)
						processing_pid = None
					except AssertionError as error:
						if str(error) == IrMailServer.NO_VALID_RECIPIENT:
							# if we have a list of void emails for email_list -> email missing, otherwise generic email failure
							if not email.get('email_to') and failure_type != "RECIPIENT":
								failure_type = "mail_email_missing"
							else:
								failure_type = "mail_email_invalid"
							# No valid recipient found for this particular
							# mail item -> ignore error to avoid blocking
							# delivery to next recipients, if any. If this is
							# the only recipient, the mail will show as failed.
							_logger.info("Ignoring invalid recipients for mail.mail %s: %s",
										 mail.message_id, email.get('email_to'))
						else:
							raise
				if res:  # mail has been sent at least once, no major exception occured
					mail.write({'state': 'sent', 'message_id': res, 'failure_reason': False})
					_logger.info('Mail with ID %r and Message-Id %r successfully sent', mail.id, mail.message_id)
					# /!\ can't use mail.state here, as mail.refresh() will cause an error
					# see revid:odo@openerp.com-20120622152536-42b2s28lvdv3odyr in 6.1
				mail._postprocess_sent_message(success_pids=success_pids, failure_type=failure_type)
			except MemoryError:
				# prevent catching transient MemoryErrors, bubble up to notify user or abort cron job
				# instead of marking the mail as failed
				_logger.exception(
					'MemoryError while processing mail with ID %r and Msg-Id %r. Consider raising the --limit-memory-hard startup option',
					mail.id, mail.message_id)
				# mail status will stay on ongoing since transaction will be rollback
				raise
			except (psycopg2.Error, smtplib.SMTPServerDisconnected):
				# If an error with the database or SMTP session occurs, chances are that the cursor
				# or SMTP session are unusable, causing further errors when trying to save the state.
				_logger.exception(
					'Exception while processing mail with ID %r and Msg-Id %r.',
					mail.id, mail.message_id)
				raise
			except Exception as e:
				failure_reason = tools.ustr(e)
				_logger.exception('failed sending mail (id: %s) due to %s', mail.id, failure_reason)
				mail.write({'state': 'exception', 'failure_reason': failure_reason})
				mail._postprocess_sent_message(success_pids=success_pids, failure_reason=failure_reason, failure_type='unknown')
				if raise_exception:
					if isinstance(e, (AssertionError, UnicodeEncodeError)):
						if isinstance(e, UnicodeEncodeError):
							value = "Invalid text: %s" % e.object
						else:
							value = '. '.join(e.args)
						raise MailDeliveryException(value)
					raise

			if auto_commit is True:
				self._cr.commit()
		return True


class Message(models.Model):
	_inherit = 'mail.message'

	partner_cc_ids = fields.Many2many(
		'res.partner', 'mail_message_cc_res_partner_rel',
		'message_id', 'partner_id', 'CC (Recipients)')

	partner_bcc_ids = fields.Many2many(
		'res.partner', 'mail_message_bcc_res_partner_rel',
		'message_id', 'partner_id', 'BCC (Recipients)')

	cc_visible = fields.Boolean('Enable Email CC')
	bcc_visible = fields.Boolean('Enable Email BCC')

class MailThread(models.AbstractModel):
	_inherit = 'mail.thread'

	@api.returns('mail.message', lambda value: value.id)
	def message_post(self, *,
					 body='', subject=None, message_type='notification',
					 email_from=None, author_id=None, parent_id=False,
					 subtype_xmlid=None, subtype_id=False, partner_ids=None,
					 attachments=None, attachment_ids=None,
					 add_sign=True, record_name=False,
					 **kwargs):
		""" Post a new message in an existing thread, returning the new
			mail.message ID.
			:param str body: body of the message, usually raw HTML that will
				be sanitized
			:param str subject: subject of the message
			:param str message_type: see mail_message.message_type field. Can be anything but
				user_notification, reserved for message_notify
			:param int parent_id: handle thread formation
			:param int subtype_id: subtype_id of the message, used mainly use for
				followers notification mechanism;
			:param list(int) partner_ids: partner_ids to notify in addition to partners
				computed based on subtype / followers matching;
			:param list(tuple(str,str), tuple(str,str, dict) or int) attachments : list of attachment tuples in the form
				``(name,content)`` or ``(name,content, info)``, where content is NOT base64 encoded
			:param list id attachment_ids: list of existing attachement to link to this message
				-Should only be setted by chatter
				-Attachement object attached to mail.compose.message(0) will be attached
					to the related document.
			Extra keyword arguments will be used as default column values for the
			new mail.message record.
			:return int: ID of newly created mail.message
		"""
		self.ensure_one()  # should always be posted on a record, use message_notify if no record
		# split message additional values from notify additional values
		msg_kwargs = dict((key, val) for key, val in kwargs.items() if key in self.env['mail.message']._fields)
		notif_kwargs = dict((key, val) for key, val in kwargs.items() if key not in msg_kwargs)

		# preliminary value safety check
		partner_ids = set(partner_ids or [])
		if self._name == 'mail.thread' or not self.id or message_type == 'user_notification':
			raise ValueError(_('Posting a message should be done on a business document. Use message_notify to send a notification to an user.'))
		if 'channel_ids' in kwargs:
			raise ValueError(_("Posting a message with channels as listeners is not supported since Odoo 14.3+. Please update code accordingly."))
		if 'model' in msg_kwargs or 'res_id' in msg_kwargs:
			raise ValueError(_("message_post does not support model and res_id parameters anymore. Please call message_post on record."))
		if 'subtype' in kwargs:
			raise ValueError(_("message_post does not support subtype parameter anymore. Please give a valid subtype_id or subtype_xmlid value instead."))
		if any(not isinstance(pc_id, int) for pc_id in partner_ids):
			raise ValueError(_('message_post partner_ids and must be integer list, not commands.'))

		self = self._fallback_lang() # add lang to context imediatly since it will be usefull in various flows latter.

		# Explicit access rights check, because display_name is computed as sudo.
		self.check_access_rights('read')
		self.check_access_rule('read')
		record_name = record_name or self.display_name

		# Find the message's author
		if self.env.user._is_public() and 'guest' in self.env.context:
			author_guest_id = self.env.context['guest'].id
			author_id, email_from = False, False
		else:
			author_guest_id = False
			author_id, email_from = self._message_compute_author(author_id, email_from, raise_exception=True)

		if subtype_xmlid:
			subtype_id = self.env['ir.model.data']._xmlid_to_res_id(subtype_xmlid)
		if not subtype_id:
			subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note')

		# automatically subscribe recipients if asked to
		if self._context.get('mail_post_autofollow') and partner_ids:
			self.message_subscribe(partner_ids=list(partner_ids))

		parent_id = self._message_compute_parent_id(parent_id)

		values = dict(msg_kwargs)

		# Added CC AND BCC In Mail Message
		partner_cc_ids = set()
		kwargs_partner_cc_ids = kwargs.pop('partner_cc_ids', [])
		for partner_id in kwargs_partner_cc_ids:
			partner_cc_ids.add(partner_id)

		partner_bcc_ids = set()
		kwargs_partner_bcc_ids = kwargs.pop('partner_bcc_ids', [])
		for partner_id in kwargs_partner_bcc_ids:
			partner_bcc_ids.add(partner_id)

		cc_visible = kwargs.get('cc_visible')
		bcc_visible = kwargs.get('bcc_visible')
		if cc_visible:
			values.update({
				'partner_cc_ids': [(4, pccid) for pccid in partner_cc_ids],
			})
		else:
			values.update({
				'partner_cc_ids': [],
			})
		if bcc_visible:
			values.update({
				'partner_bcc_ids': [(4, pbccid) for pbccid in partner_bcc_ids],
			})
		else:
			values.update({
				'partner_bcc_ids': [],
			})

		values.update({
			'author_id': author_id,
			'author_guest_id': author_guest_id,
			'email_from': email_from,
			'model': self._name,
			'res_id': self.id,
			'body': body,
			'subject': subject or False,
			'message_type': message_type,
			'parent_id': parent_id,
			'subtype_id': subtype_id,
			'partner_ids': partner_ids,
			'add_sign': add_sign,
			'cc_visible': cc_visible,
			'bcc_visible': bcc_visible,
			'record_name': record_name,
		})
		attachments = attachments or []
		attachment_ids = attachment_ids or []
		attachement_values = self._message_post_process_attachments(attachments, attachment_ids, values)
		values.update(attachement_values)  # attachement_ids, [body]

		new_message = self._message_create(values)

		# Set main attachment field if necessary
		self._message_set_main_attachment_id(values['attachment_ids'])

		if values['author_id'] and values['message_type'] != 'notification' and not self._context.get('mail_create_nosubscribe'):
			if self.env['res.partner'].browse(values['author_id']).active:  # we dont want to add odoobot/inactive as a follower
				self._message_subscribe(partner_ids=[values['author_id']])

		self._message_post_after_hook(new_message, values)
		self._notify_thread(new_message, values, **notif_kwargs)
		return new_message


	def _notify_record_by_email(self, message, recipients_data, msg_vals=False,
								model_description=False, mail_auto_delete=True, check_existing=False,
								force_send=True, send_after_commit=True,
								**kwargs):
		""" Method to send email linked to notified messages.

		:param message: mail.message record to notify;
		:param recipients_data: see ``_notify_thread``;
		:param msg_vals: see ``_notify_thread``;

		:param model_description: model description used in email notification process
		  (computed if not given);
		:param mail_auto_delete: delete notification emails once sent;
		:param check_existing: check for existing notifications to update based on
		  mailed recipient, otherwise create new notifications;

		:param force_send: send emails directly instead of using queue;
		:param send_after_commit: if force_send, tells whether to send emails after
		  the transaction has been committed using a post-commit hook;
		"""
		partners_data = [r for r in recipients_data if r['notif'] == 'email']
		if not partners_data:
			return True

		model = msg_vals.get('model') if msg_vals else message.model
		model_name = model_description or (self._fallback_lang().env['ir.model']._get(model).display_name if model else False) # one query for display name
		recipients_groups_data = self._notify_classify_recipients(partners_data, model_name, msg_vals=msg_vals)

		if not recipients_groups_data:
			return True
		force_send = self.env.context.get('mail_notify_force_send', force_send)

		template_values = self._notify_prepare_template_context(message, msg_vals, model_description=model_description) # 10 queries

		email_layout_xmlid = msg_vals.get('email_layout_xmlid') if msg_vals else message.email_layout_xmlid
		template_xmlid = email_layout_xmlid if email_layout_xmlid else 'mail.message_notification_email'
		try:
			base_template = self.env.ref(template_xmlid, raise_if_not_found=True).with_context(lang=template_values['lang']) # 1 query
		except ValueError:
			_logger.warning('QWeb template %s not found when sending notification emails. Sending without layouting.' % (template_xmlid))
			base_template = False

		mail_subject = message.subject or (message.record_name and 'Re: %s' % message.record_name) # in cache, no queries
		# Replace new lines by spaces to conform to email headers requirements
		mail_subject = ' '.join((mail_subject or '').splitlines())
		# prepare notification mail values
		base_mail_values = {
			'mail_message_id': message.id,
			'mail_server_id': message.mail_server_id.id, # 2 query, check acces + read, may be useless, Falsy, when will it be used?
			'auto_delete': mail_auto_delete,
			# due to ir.rule, user have no right to access parent message if message is not published
			'references': message.parent_id.sudo().message_id if message.parent_id else False,
			'subject': mail_subject,
		}
		base_mail_values = self._notify_by_email_add_values(base_mail_values)

		# Clean the context to get rid of residual default_* keys that could cause issues during
		# the mail.mail creation.
		# Example: 'default_state' would refer to the default state of a previously created record
		# from another model that in turns triggers an assignation notification that ends up here.
		# This will lead to a traceback when trying to create a mail.mail with this state value that
		# doesn't exist.
		SafeMail = self.env['mail.mail'].sudo().with_context(clean_context(self._context))
		SafeNotification = self.env['mail.notification'].sudo().with_context(clean_context(self._context))
		emails = self.env['mail.mail'].sudo()

		# loop on groups (customer, portal, user,  ... + model specific like group_sale_salesman)
		notif_create_values = []
		recipients_max = 50
		for recipients_group_data in recipients_groups_data:
			# generate notification email content
			recipients_ids = recipients_group_data.pop('recipients')
			render_values = {**template_values, **recipients_group_data}
			# {company, is_discussion, lang, message, model_description, record, record_name, signature, subtype, tracking_values, website_url}
			# {actions, button_access, has_button_access, recipients}

			if base_template:
				mail_body = base_template._render(render_values, engine='ir.qweb', minimal_qcontext=True)
			else:
				mail_body = message.body
			mail_body = self.env['mail.render.mixin']._replace_local_links(mail_body)

			# create email
			for recipients_ids_chunk in split_every(recipients_max, recipients_ids):
				recipient_values = self._notify_email_recipient_values(recipients_ids_chunk)
				email_to = recipient_values['email_to']
				recipient_ids = recipient_values['recipient_ids']

				create_values = {
					'body_html': mail_body,
					'subject': mail_subject,
					'recipient_ids': [Command.link(pid) for pid in recipient_ids],
				}
				if email_to:
					create_values['email_to'] = email_to

				if message.cc_visible:
					create_values.update({'recipient_cc_ids': [(4, pccid.id) for pccid in message.partner_cc_ids]})
				else:
					create_values.update({'recipient_cc_ids': []})

				if message.bcc_visible:
					create_values.update({'recipient_bcc_ids': [(4, pbccid.id) for pbccid in message.partner_bcc_ids]})
				else:
					create_values.update({'recipient_bcc_ids': []})

				create_values.update(base_mail_values)  # mail_message_id, mail_server_id, auto_delete, references, headers
				email = SafeMail.create(create_values)

				if email and recipient_ids:
					tocreate_recipient_ids = list(recipient_ids)
					if check_existing:
						existing_notifications = self.env['mail.notification'].sudo().search([
							('mail_message_id', '=', message.id),
							('notification_type', '=', 'email'),
							('res_partner_id', 'in', tocreate_recipient_ids)
						])
						if existing_notifications:
							tocreate_recipient_ids = [rid for rid in recipient_ids if rid not in existing_notifications.mapped('res_partner_id.id')]
							existing_notifications.write({
								'notification_status': 'ready',
								'mail_mail_id': email.id,
							})
					notif_create_values += [{
						'mail_message_id': message.id,
						'res_partner_id': recipient_id,
						'notification_type': 'email',
						'mail_mail_id': email.id,
						'is_read': True,  # discard Inbox notification
						'notification_status': 'ready',
					} for recipient_id in tocreate_recipient_ids]
				emails |= email

		if notif_create_values:
			SafeNotification.create(notif_create_values)

		# NOTE:
		#   1. for more than 50 followers, use the queue system
		#   2. do not send emails immediately if the registry is not loaded,
		#      to prevent sending email during a simple update of the database
		#      using the command-line.
		test_mode = getattr(threading.currentThread(), 'testing', False)
		if force_send and len(emails) < recipients_max and (not self.pool._init or test_mode):
			# unless asked specifically, send emails after the transaction to
			# avoid side effects due to emails being sent while the transaction fails
			if not test_mode and send_after_commit:
				email_ids = emails.ids
				dbname = self.env.cr.dbname
				_context = self._context

				@self.env.cr.postcommit.add
				def send_notifications():
					db_registry = registry(dbname)
					with db_registry.cursor() as cr:
						env = api.Environment(cr, SUPERUSER_ID, _context)
						env['mail.mail'].browse(email_ids).send()
			else:
				emails.send()

		return True



