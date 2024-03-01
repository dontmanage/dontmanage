# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

from typing import Protocol, runtime_checkable

import dontmanage
from dontmanage import _
from dontmanage.model.base_document import get_controller
from dontmanage.model.document import Document
from dontmanage.utils import cint
from dontmanage.utils.caching import site_cache


@runtime_checkable
class LogType(Protocol):
	"""Interface requirement for doctypes that can be cleared using log settings."""

	@staticmethod
	def clear_old_logs(days: int) -> None:
		...


@site_cache
def _supports_log_clearing(doctype: str) -> bool:
	try:
		controller = get_controller(doctype)
		return issubclass(controller, LogType)
	except Exception:
		return False


class LogSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.core.doctype.logs_to_clear.logs_to_clear import LogsToClear
		from dontmanage.types import DF

		logs_to_clear: DF.Table[LogsToClear]

	# end: auto-generated types
	def validate(self):
		self.remove_unsupported_doctypes()
		self._deduplicate_entries()
		self.add_default_logtypes()

	def remove_unsupported_doctypes(self):
		for entry in list(self.logs_to_clear):
			if _supports_log_clearing(entry.ref_doctype):
				continue

			msg = _("{} does not support automated log clearing.").format(dontmanage.bold(entry.ref_doctype))
			if dontmanage.conf.developer_mode:
				msg += "<br>" + _("Implement `clear_old_logs` method to enable auto error clearing.")
			dontmanage.msgprint(msg, title=_("DocType not supported by Log Settings."))
			self.remove(entry)

	def _deduplicate_entries(self):
		seen = set()
		for entry in list(self.logs_to_clear):
			if entry.ref_doctype in seen:
				self.remove(entry)
			seen.add(entry.ref_doctype)

	def add_default_logtypes(self):
		existing_logtypes = {d.ref_doctype for d in self.logs_to_clear}
		added_logtypes = set()
		default_logtypes_retention = dontmanage.get_hooks("default_log_clearing_doctypes", {})

		for logtype, retentions in default_logtypes_retention.items():
			if logtype not in existing_logtypes and _supports_log_clearing(logtype):
				if not dontmanage.db.exists("DocType", logtype):
					continue

				self.append("logs_to_clear", {"ref_doctype": logtype, "days": cint(retentions[-1])})
				added_logtypes.add(logtype)

		if added_logtypes:
			dontmanage.msgprint(_("Added default log doctypes: {}").format(",".join(added_logtypes)), alert=True)

	def clear_logs(self):
		"""
		Log settings can clear any log type that's registered to it and provides a method to delete old logs.

		Check `LogDoctype` above for interface that doctypes need to implement.
		"""

		for entry in self.logs_to_clear:
			controller: LogType = get_controller(entry.ref_doctype)
			func = controller.clear_old_logs

			# Only pass what the method can handle, this is considering any
			# future addition that might happen to the required interface.
			kwargs = dontmanage.get_newargs(func, {"days": entry.days})
			func(**kwargs)
			dontmanage.db.commit()

	def register_doctype(self, doctype: str, days=30):
		existing_logtypes = {d.ref_doctype for d in self.logs_to_clear}

		if doctype not in existing_logtypes and _supports_log_clearing(doctype):
			self.append("logs_to_clear", {"ref_doctype": doctype, "days": cint(days)})
		else:
			for entry in self.logs_to_clear:
				if entry.ref_doctype == doctype:
					entry.days = days
					break


def run_log_clean_up():
	doc = dontmanage.get_doc("Log Settings")
	doc.remove_unsupported_doctypes()
	doc.add_default_logtypes()
	doc.save()
	doc.clear_logs()


@dontmanage.whitelist()
def has_unseen_error_log():
	if dontmanage.get_all("Error Log", filters={"seen": 0}, limit=1):
		return {
			"show_alert": True,
			"message": _("You have unseen {0}").format(
				'<a href="/app/List/Error%20Log/List"> Error Logs </a>'
			),
		}


@dontmanage.whitelist()
@dontmanage.validate_and_sanitize_search_inputs
def get_log_doctypes(doctype, txt, searchfield, start, page_len, filters):
	filters = filters or {}

	filters.extend(
		[
			["istable", "=", 0],
			["issingle", "=", 0],
			["name", "like", f"%%{txt}%%"],
		]
	)
	doctypes = dontmanage.get_list("DocType", filters=filters, pluck="name")

	supported_doctypes = [(d,) for d in doctypes if _supports_log_clearing(d)]

	return supported_doctypes[start:page_len]


LOG_DOCTYPES = [
	"Scheduled Job Log",
	"Activity Log",
	"Route History",
	"Email Queue",
	"Email Queue Recipient",
	"Error Log",
]


def clear_log_table(doctype, days=90):
	"""If any logtype table grows too large then clearing it with DELETE query
	is not feasible in reasonable time. This command copies recent data to new
	table and replaces current table with new smaller table.

	ref: https://mariadb.com/kb/en/big-deletes/#deleting-more-than-half-a-table
	"""
	from dontmanage.utils import get_table_name

	if doctype not in LOG_DOCTYPES:
		raise dontmanage.ValidationError(f"Unsupported logging DocType: {doctype}")

	original = get_table_name(doctype)
	temporary = f"{original} temp_table"
	backup = f"{original} backup_table"

	try:
		dontmanage.db.sql_ddl(f"CREATE TABLE `{temporary}` LIKE `{original}`")

		# Copy all recent data to new table
		dontmanage.db.sql(
			f"""INSERT INTO `{temporary}`
				SELECT * FROM `{original}`
				WHERE `{original}`.`modified` > NOW() - INTERVAL '{days}' DAY"""
		)
		dontmanage.db.sql_ddl(f"RENAME TABLE `{original}` TO `{backup}`, `{temporary}` TO `{original}`")
	except Exception:
		dontmanage.db.rollback()
		dontmanage.db.sql_ddl(f"DROP TABLE IF EXISTS `{temporary}`")
		raise
	else:
		dontmanage.db.sql_ddl(f"DROP TABLE `{backup}`")
