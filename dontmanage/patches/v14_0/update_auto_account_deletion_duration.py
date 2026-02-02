import dontmanage


def execute():
	days = dontmanage.db.get_single_value("Website Settings", "auto_account_deletion")
	dontmanage.db.set_single_value("Website Settings", "auto_account_deletion", days * 24)
