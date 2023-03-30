import dontmanage

from ..role import desk_properties


def execute():
	for role in dontmanage.get_all("Role", ["name", "desk_access"]):
		role_doc = dontmanage.get_doc("Role", role.name)
		for key in desk_properties:
			role_doc.set(key, role_doc.desk_access)
		role_doc.save()
