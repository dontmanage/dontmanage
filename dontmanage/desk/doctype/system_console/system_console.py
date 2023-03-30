# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage.model.document import Document
from dontmanage.utils.safe_exec import read_sql, safe_exec


class SystemConsole(Document):
	def run(self):
		dontmanage.only_for("System Manager")
		try:
			dontmanage.local.debug_log = []
			if self.type == "Python":
				safe_exec(self.console)
				self.output = "\n".join(dontmanage.debug_log)
			elif self.type == "SQL":
				self.output = dontmanage.as_json(read_sql(self.console, as_dict=1))
		except Exception:
			self.output = dontmanage.get_traceback()

		if self.commit:
			dontmanage.db.commit()
		else:
			dontmanage.db.rollback()

		dontmanage.get_doc(dict(doctype="Console Log", script=self.console, output=self.output)).insert()
		dontmanage.db.commit()


@dontmanage.whitelist()
def execute_code(doc):
	console = dontmanage.get_doc(json.loads(doc))
	console.run()
	return console.as_dict()


@dontmanage.whitelist()
def show_processlist():
	dontmanage.only_for("System Manager")

	return dontmanage.db.multisql(
		{
			"postgres": """
			SELECT pid AS "Id",
				query_start AS "Time",
				state AS "State",
				query AS "Info",
				wait_event AS "Progress"
			FROM pg_stat_activity""",
			"mariadb": "show full processlist",
		},
		as_dict=True,
	)
