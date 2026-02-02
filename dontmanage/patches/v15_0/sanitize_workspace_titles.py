import dontmanage
from dontmanage.desk.doctype.workspace.workspace import update_page
from dontmanage.utils import strip_html
from dontmanage.utils.html_utils import unescape_html


def execute():
	workspaces_to_update = dontmanage.get_all(
		"Workspace",
		filters={"module": ("is", "not set")},
		fields=["name", "title", "icon", "indicator_color", "parent_page as parent", "public"],
	)
	for workspace in workspaces_to_update:
		new_title = strip_html(unescape_html(workspace.title))

		if new_title == workspace.title:
			continue

		workspace.title = new_title
		try:
			update_page(**workspace)
			dontmanage.db.commit()

		except Exception:
			dontmanage.db.rollback()
