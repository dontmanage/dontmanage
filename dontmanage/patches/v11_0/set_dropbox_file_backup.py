import dontmanage
from dontmanage.utils import cint


def execute():
	dontmanage.reload_doctype("Dropbox Settings")
	check_dropbox_enabled = cint(dontmanage.db.get_single_value("Dropbox Settings", "enabled"))
	if check_dropbox_enabled == 1:
		dontmanage.db.set_single_value("Dropbox Settings", "file_backup", 1)
