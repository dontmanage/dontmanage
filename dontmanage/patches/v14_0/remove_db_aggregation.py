import re

import dontmanage
from dontmanage.query_builder import DocType


def execute():
	"""Replace temporarily available Database Aggregate APIs on dontmanage (develop)

	APIs changed:
	        * dontmanage.db.max => dontmanage.qb.max
	        * dontmanage.db.min => dontmanage.qb.min
	        * dontmanage.db.sum => dontmanage.qb.sum
	        * dontmanage.db.avg => dontmanage.qb.avg
	"""
	ServerScript = DocType("Server Script")
	server_scripts = (
		dontmanage.qb.from_(ServerScript)
		.where(
			ServerScript.script.like("%dontmanage.db.max(%")
			| ServerScript.script.like("%dontmanage.db.min(%")
			| ServerScript.script.like("%dontmanage.db.sum(%")
			| ServerScript.script.like("%dontmanage.db.avg(%")
		)
		.select("name", "script")
		.run(as_dict=True)
	)

	for server_script in server_scripts:
		name, script = server_script["name"], server_script["script"]

		for agg in ["avg", "max", "min", "sum"]:
			script = re.sub(f"dontmanage.db.{agg}\\(", f"dontmanage.qb.{agg}(", script)

		dontmanage.db.set_value("Server Script", name, "script", script)
