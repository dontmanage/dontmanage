import dontmanage


def update_system_settings(args, commit=False):
	doc = dontmanage.get_doc("System Settings")
	doc.update(args)
	doc.flags.ignore_mandatory = 1
	doc.save()
	if commit:
		dontmanage.db.commit()


def get_system_setting(key):
	return dontmanage.db.get_single_value("System Settings", key)


global_test_dependencies = ["User"]
