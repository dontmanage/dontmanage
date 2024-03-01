# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage

# import dontmanage
from dontmanage.model.document import Document


class DashboardSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		chart_config: DF.Code | None
		user: DF.Link | None
	# end: auto-generated types
	pass


@dontmanage.whitelist()
def create_dashboard_settings(user):
	if not dontmanage.db.exists("Dashboard Settings", user):
		doc = dontmanage.new_doc("Dashboard Settings")
		doc.name = user
		doc.insert(ignore_permissions=True)
		dontmanage.db.commit()
		return doc


def get_permission_query_conditions(user):
	if not user:
		user = dontmanage.session.user

	return f"""(`tabDashboard Settings`.name = {dontmanage.db.escape(user)})"""


@dontmanage.whitelist()
def save_chart_config(reset, config, chart_name):
	reset = dontmanage.parse_json(reset)
	doc = dontmanage.get_doc("Dashboard Settings", dontmanage.session.user)
	chart_config = dontmanage.parse_json(doc.chart_config) or {}

	if reset:
		chart_config[chart_name] = {}
	else:
		config = dontmanage.parse_json(config)
		if chart_name not in chart_config:
			chart_config[chart_name] = {}
		chart_config[chart_name].update(config)

	dontmanage.db.set_value("Dashboard Settings", dontmanage.session.user, "chart_config", json.dumps(chart_config))
