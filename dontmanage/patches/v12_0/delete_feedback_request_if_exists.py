import dontmanage


def execute():
	dontmanage.db.delete("DocType", {"name": "Feedback Request"})
