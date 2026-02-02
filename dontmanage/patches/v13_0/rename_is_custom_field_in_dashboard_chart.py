import dontmanage
from dontmanage.model.utils.rename_field import rename_field


def execute():
	if not dontmanage.db.table_exists("Dashboard Chart"):
		return

	dontmanage.reload_doc("desk", "doctype", "dashboard_chart")

	if dontmanage.db.has_column("Dashboard Chart", "is_custom"):
		rename_field("Dashboard Chart", "is_custom", "use_report_chart")
