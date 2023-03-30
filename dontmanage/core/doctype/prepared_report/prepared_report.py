# Copyright (c) 2018, DontManage Technologies and contributors
# License: MIT. See LICENSE


import json

import dontmanage
from dontmanage.desk.form.load import get_attachments
from dontmanage.desk.query_report import generate_report_result
from dontmanage.model.document import Document
from dontmanage.monitor import add_data_to_monitor
from dontmanage.utils import gzip_compress, gzip_decompress
from dontmanage.utils.background_jobs import enqueue


class PreparedReport(Document):
	def before_insert(self):
		self.status = "Queued"
		self.report_start_time = dontmanage.utils.now()

	def enqueue_report(self):
		enqueue(run_background, prepared_report=self.name, timeout=6000)


def run_background(prepared_report):
	instance = dontmanage.get_doc("Prepared Report", prepared_report)
	report = dontmanage.get_doc("Report", instance.ref_report_doctype)

	add_data_to_monitor(report=instance.ref_report_doctype)

	try:
		report.custom_columns = []

		if report.report_type == "Custom Report":
			custom_report_doc = report
			reference_report = custom_report_doc.reference_report
			report = dontmanage.get_doc("Report", reference_report)
			if custom_report_doc.json:
				data = json.loads(custom_report_doc.json)
				if data:
					report.custom_columns = data["columns"]

		result = generate_report_result(report=report, filters=instance.filters, user=instance.owner)
		create_json_gz_file(result["result"], "Prepared Report", instance.name)

		instance.status = "Completed"
		instance.columns = json.dumps(result["columns"])
		instance.report_end_time = dontmanage.utils.now()
		instance.save(ignore_permissions=True)

	except Exception:
		report.log_error("Prepared report failed")
		instance = dontmanage.get_doc("Prepared Report", prepared_report)
		instance.status = "Error"
		instance.error_message = dontmanage.get_traceback()
		instance.save(ignore_permissions=True)

	dontmanage.publish_realtime(
		"report_generated",
		{"report_name": instance.report_name, "name": instance.name},
		user=dontmanage.session.user,
	)


@dontmanage.whitelist()
def get_reports_in_queued_state(report_name, filters):
	reports = dontmanage.get_all(
		"Prepared Report",
		filters={
			"report_name": report_name,
			"filters": process_filters_for_prepared_report(filters),
			"status": "Queued",
		},
	)
	return reports


def delete_expired_prepared_reports():
	system_settings = dontmanage.get_single("System Settings")
	enable_auto_deletion = system_settings.enable_prepared_report_auto_deletion
	if enable_auto_deletion:
		expiry_period = system_settings.prepared_report_expiry_period
		prepared_reports_to_delete = dontmanage.get_all(
			"Prepared Report",
			filters={"creation": ["<", dontmanage.utils.add_days(dontmanage.utils.now(), -expiry_period)]},
		)

		batches = dontmanage.utils.create_batch(prepared_reports_to_delete, 100)
		for batch in batches:
			args = {
				"reports": batch,
			}
			enqueue(method=delete_prepared_reports, job_name="delete_prepared_reports", **args)


@dontmanage.whitelist()
def delete_prepared_reports(reports):
	reports = dontmanage.parse_json(reports)
	for report in reports:
		dontmanage.delete_doc(
			"Prepared Report", report["name"], ignore_permissions=True, delete_permanently=True
		)


def process_filters_for_prepared_report(filters):
	if isinstance(filters, str):
		filters = json.loads(filters)

	# This looks like an insanity but, without this it'd be very hard to find Prepared Reports matching given condition
	# We're ensuring that spacing is consistent. e.g. JS seems to put no spaces after ":", Python on the other hand does.
	# We are also ensuring that order of keys is same so generated JSON string will be identical too.
	# PS: dontmanage.as_json sorts keys
	return dontmanage.as_json(filters, indent=None, separators=(",", ":"))


def create_json_gz_file(data, dt, dn):
	# Storing data in CSV file causes information loss
	# Reports like P&L Statement were completely unsuable because of this
	json_filename = "{}.json.gz".format(
		dontmanage.utils.data.format_datetime(dontmanage.utils.now(), "Y-m-d-H:M")
	)
	encoded_content = dontmanage.safe_encode(dontmanage.as_json(data))
	compressed_content = gzip_compress(encoded_content)

	# Call save() file function to upload and attach the file
	_file = dontmanage.get_doc(
		{
			"doctype": "File",
			"file_name": json_filename,
			"attached_to_doctype": dt,
			"attached_to_name": dn,
			"content": compressed_content,
			"is_private": 1,
		}
	)
	_file.save(ignore_permissions=True)


@dontmanage.whitelist()
def download_attachment(dn):
	attachment = get_attachments("Prepared Report", dn)[0]
	dontmanage.local.response.filename = attachment.file_name[:-2]
	attached_file = dontmanage.get_doc("File", attachment.name)
	dontmanage.local.response.filecontent = gzip_decompress(attached_file.get_content())
	dontmanage.local.response.type = "binary"


def get_permission_query_condition(user):
	if not user:
		user = dontmanage.session.user
	if user == "Administrator":
		return None

	from dontmanage.utils.user import UserPermissions

	user = UserPermissions(user)

	if "System Manager" in user.roles:
		return None

	reports = [dontmanage.db.escape(report) for report in user.get_all_reports().keys()]

	return """`tabPrepared Report`.ref_report_doctype in ({reports})""".format(
		reports=",".join(reports)
	)


def has_permission(doc, user):
	if not user:
		user = dontmanage.session.user
	if user == "Administrator":
		return True

	from dontmanage.utils.user import UserPermissions

	user = UserPermissions(user)

	if "System Manager" in user.roles:
		return True

	return doc.ref_report_doctype in user.get_all_reports().keys()
