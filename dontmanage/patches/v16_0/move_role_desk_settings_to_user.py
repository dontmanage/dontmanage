# Copyright (c) 2023, DontManage and Contributors
# MIT License. See license.txt

import dontmanage
from dontmanage.core.doctype.user.user import desk_properties


def execute():
	roles = {role.name: role for role in dontmanage.get_all("Role", fields=["*"])}

	for user in dontmanage.get_list("User"):
		user_desk_settings = {}
		for role_name in dontmanage.get_roles(username=user.name):
			if role := roles.get(role_name):
				for key in desk_properties:
					if role.get(key) is None:
						role[key] = 1
					user_desk_settings[key] = user_desk_settings.get(key) or role.get(key)

		dontmanage.db.set_value("User", user.name, user_desk_settings)
