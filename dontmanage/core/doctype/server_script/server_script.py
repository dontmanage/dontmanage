# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

from types import FunctionType, MethodType, ModuleType

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document
from dontmanage.utils.safe_exec import NamespaceDict, get_safe_globals, safe_exec


class ServerScript(Document):
	def validate(self):
		dontmanage.only_for("Script Manager", True)
		self.sync_scheduled_jobs()
		self.clear_scheduled_events()
		self.check_if_compilable_in_restricted_context()

	def on_update(self):
		dontmanage.cache().delete_value("server_script_map")
		self.sync_scheduler_events()

	def on_trash(self):
		if self.script_type == "Scheduler Event":
			for job in self.scheduled_jobs:
				dontmanage.delete_doc("Scheduled Job Type", job.name)

	def get_code_fields(self):
		return {"script": "py"}

	@property
	def scheduled_jobs(self) -> list[dict[str, str]]:
		return dontmanage.get_all(
			"Scheduled Job Type",
			filters={"server_script": self.name},
			fields=["name", "stopped"],
		)

	def sync_scheduled_jobs(self):
		"""Sync Scheduled Job Type statuses if Server Script's disabled status is changed"""
		if self.script_type != "Scheduler Event" or not self.has_value_changed("disabled"):
			return

		for scheduled_job in self.scheduled_jobs:
			if bool(scheduled_job.stopped) != bool(self.disabled):
				job = dontmanage.get_doc("Scheduled Job Type", scheduled_job.name)
				job.stopped = self.disabled
				job.save()

	def sync_scheduler_events(self):
		"""Create or update Scheduled Job Type documents for Scheduler Event Server Scripts"""
		if not self.disabled and self.event_frequency and self.script_type == "Scheduler Event":
			setup_scheduler_events(script_name=self.name, frequency=self.event_frequency)

	def clear_scheduled_events(self):
		"""Deletes existing scheduled jobs by Server Script if self.event_frequency has changed"""
		if self.script_type == "Scheduler Event" and self.has_value_changed("event_frequency"):
			for scheduled_job in self.scheduled_jobs:
				dontmanage.delete_doc("Scheduled Job Type", scheduled_job.name)

	def check_if_compilable_in_restricted_context(self):
		"""Check compilation errors and send them back as warnings."""
		from RestrictedPython import compile_restricted

		try:
			compile_restricted(self.script)
		except Exception as e:
			dontmanage.msgprint(str(e), title=_("Compilation warning"))

	def execute_method(self) -> dict:
		"""Specific to API endpoint Server Scripts

		Raises:
		        dontmanage.DoesNotExistError: If self.script_type is not API
		        dontmanage.PermissionError: If self.allow_guest is unset for API accessed by Guest user

		Returns:
		        dict: Evaluates self.script with dontmanage.utils.safe_exec.safe_exec and returns the flags set in it's safe globals
		"""
		# wrong report type!
		if self.script_type != "API":
			raise dontmanage.DoesNotExistError

		# validate if guest is allowed
		if dontmanage.session.user == "Guest" and not self.allow_guest:
			raise dontmanage.PermissionError

		# output can be stored in flags
		_globals, _locals = safe_exec(self.script)
		return _globals.dontmanage.flags

	def execute_doc(self, doc: Document):
		"""Specific to Document Event triggered Server Scripts

		Args:
		        doc (Document): Executes script with for a certain document's events
		"""
		safe_exec(self.script, _locals={"doc": doc}, restrict_commit_rollback=True)

	def execute_scheduled_method(self):
		"""Specific to Scheduled Jobs via Server Scripts

		Raises:
		        dontmanage.DoesNotExistError: If script type is not a scheduler event
		"""
		if self.script_type != "Scheduler Event":
			raise dontmanage.DoesNotExistError

		safe_exec(self.script)

	def get_permission_query_conditions(self, user: str) -> list[str]:
		"""Specific to Permission Query Server Scripts

		Args:
		        user (str): Takes user email to execute script and return list of conditions

		Returns:
		        list: Returns list of conditions defined by rules in self.script
		"""
		locals = {"user": user, "conditions": ""}
		safe_exec(self.script, None, locals)
		if locals["conditions"]:
			return locals["conditions"]

	@dontmanage.whitelist()
	def get_autocompletion_items(self):
		"""Generates a list of a autocompletion strings from the context dict
		that is used while executing a Server Script.

		Returns:
		        list: Returns list of autocompletion items.
		        For e.g., ["dontmanage.utils.cint", "dontmanage.get_all", ...]
		"""

		def get_keys(obj):
			out = []
			for key in obj:
				if key.startswith("_"):
					continue
				value = obj[key]
				if isinstance(value, (NamespaceDict, dict)) and value:
					if key == "form_dict":
						out.append(["form_dict", 7])
						continue
					for subkey, score in get_keys(value):
						fullkey = f"{key}.{subkey}"
						out.append([fullkey, score])
				else:
					if isinstance(value, type) and issubclass(value, Exception):
						score = 0
					elif isinstance(value, ModuleType):
						score = 10
					elif isinstance(value, (FunctionType, MethodType)):
						score = 9
					elif isinstance(value, type):
						score = 8
					elif isinstance(value, dict):
						score = 7
					else:
						score = 6
					out.append([key, score])
			return out

		items = dontmanage.cache().get_value("server_script_autocompletion_items")
		if not items:
			items = get_keys(get_safe_globals())
			items = [{"value": d[0], "score": d[1]} for d in items]
			dontmanage.cache().set_value("server_script_autocompletion_items", items)
		return items


@dontmanage.whitelist()
def setup_scheduler_events(script_name, frequency):
	"""Creates or Updates Scheduled Job Type documents based on the specified script name and frequency

	Args:
	        script_name (str): Name of the Server Script document
	        frequency (str): Event label compatible with the DontManage scheduler
	"""
	method = dontmanage.scrub(f"{script_name}-{frequency}")
	scheduled_script = dontmanage.db.get_value("Scheduled Job Type", {"method": method})

	if not scheduled_script:
		dontmanage.get_doc(
			{
				"doctype": "Scheduled Job Type",
				"method": method,
				"frequency": frequency,
				"server_script": script_name,
			}
		).insert()

		dontmanage.msgprint(_("Enabled scheduled execution for script {0}").format(script_name))

	else:
		doc = dontmanage.get_doc("Scheduled Job Type", scheduled_script)

		if doc.frequency == frequency:
			return

		doc.frequency = frequency
		doc.save()

		dontmanage.msgprint(_("Scheduled execution for script {0} has updated").format(script_name))
