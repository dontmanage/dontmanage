# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import os

import dontmanage
from dontmanage.model.document import Document
from dontmanage.modules import get_module_path, scrub
from dontmanage.modules.export_file import export_to_files


@dontmanage.whitelist()
def get_config(name):
	doc = dontmanage.get_doc("Dashboard Chart Source", name)
	with open(
		os.path.join(
			get_module_path(doc.module), "dashboard_chart_source", scrub(doc.name), scrub(doc.name) + ".js"
		),
	) as f:
		return f.read()


class DashboardChartSource(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from dontmanage.types import DF

		module: DF.Link
		source_name: DF.Data
		timeseries: DF.Check

	# end: auto-generated types
	def on_update(self):
		export_to_files(record_list=[[self.doctype, self.name]], record_module=self.module, create_init=True)
