# Copyright (c) 2017, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage


def run_webhooks(doc, method):
	"""Run webhooks for this method"""
	if (
		dontmanage.flags.in_import
		or dontmanage.flags.in_patch
		or dontmanage.flags.in_install
		or dontmanage.flags.in_migrate
	):
		return

	if dontmanage.flags.webhooks_executed is None:
		dontmanage.flags.webhooks_executed = {}

	# TODO: remove this hazardous unnecessary cache in flags
	if dontmanage.flags.webhooks is None:
		# load webhooks from cache
		webhooks = dontmanage.cache().get_value("webhooks")
		if webhooks is None:
			# query webhooks
			webhooks_list = dontmanage.get_all(
				"Webhook",
				fields=["name", "`condition`", "webhook_docevent", "webhook_doctype"],
				filters={"enabled": True},
			)

			# make webhooks map for cache
			webhooks = {}
			for w in webhooks_list:
				webhooks.setdefault(w.webhook_doctype, []).append(w)
			dontmanage.cache().set_value("webhooks", webhooks)

		dontmanage.flags.webhooks = webhooks

	# get webhooks for this doctype
	webhooks_for_doc = dontmanage.flags.webhooks.get(doc.doctype, None)

	if not webhooks_for_doc:
		# no webhooks, quit
		return

	def _webhook_request(webhook):
		if webhook.name not in dontmanage.flags.webhooks_executed.get(doc.name, []):
			dontmanage.enqueue(
				"dontmanage.integrations.doctype.webhook.webhook.enqueue_webhook",
				enqueue_after_commit=True,
				doc=doc,
				webhook=webhook,
			)

			# keep list of webhooks executed for this doc in this request
			# so that we don't run the same webhook for the same document multiple times
			# in one request
			dontmanage.flags.webhooks_executed.setdefault(doc.name, []).append(webhook.name)

	event_list = ["on_update", "after_insert", "on_submit", "on_cancel", "on_trash"]

	if not doc.flags.in_insert:
		# value change is not applicable in insert
		event_list.append("on_change")
		event_list.append("before_update_after_submit")

	from dontmanage.integrations.doctype.webhook.webhook import get_context

	for webhook in webhooks_for_doc:
		trigger_webhook = False
		event = method if method in event_list else None
		if not webhook.condition:
			trigger_webhook = True
		elif dontmanage.safe_eval(webhook.condition, eval_locals=get_context(doc)):
			trigger_webhook = True

		if trigger_webhook and event and webhook.webhook_docevent == event:
			_webhook_request(webhook)
