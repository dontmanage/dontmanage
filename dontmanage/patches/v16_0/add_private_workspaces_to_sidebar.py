import click

import dontmanage


def execute():
	from dontmanage.query_builder import DocType

	workspace = DocType("Workspace")
	all_workspaces = (dontmanage.qb.from_(workspace).select(workspace.name).where(workspace.public == 0)).run(
		pluck=True
	)
	from dontmanage.desk.doctype.workspace_sidebar.workspace_sidebar import add_to_my_workspace

	for space in all_workspaces:
		workspace_doc = dontmanage.get_doc("Workspace", space)
		add_to_my_workspace(workspace_doc)
	# save the sidebar items
	dontmanage.db.commit()  # nosemgrep
