import dontmanage
from dontmanage.desk.utils import slug


def execute():
	for doctype in dontmanage.get_all("DocType", ["name", "route"], dict(istable=0)):
		if not doctype.route:
			dontmanage.db.set_value("DocType", doctype.name, "route", slug(doctype.name), update_modified=False)
