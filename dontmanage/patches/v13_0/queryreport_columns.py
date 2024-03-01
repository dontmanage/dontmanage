# Copyright (c) 2021, DontManage and Contributors
# License: MIT. See LICENSE

import json

import dontmanage


def execute():
	"""Convert Query Report json to support other content"""
	records = dontmanage.get_all("Report", filters={"json": ["!=", ""]}, fields=["name", "json"])
	for record in records:
		jstr = record["json"]
		data = json.loads(jstr)
		if isinstance(data, list):
			# double escape braces
			jstr = f'{{"columns":{jstr}}}'
			dontmanage.db.set_value("Report", record["name"], "json", jstr)
