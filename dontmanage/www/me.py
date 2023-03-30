# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
import dontmanage.www.list
from dontmanage import _

no_cache = 1


def get_context(context):
	if dontmanage.session.user == "Guest":
		dontmanage.throw(_("You need to be logged in to access this page"), dontmanage.PermissionError)

	context.current_user = dontmanage.get_doc("User", dontmanage.session.user)
	context.show_sidebar = True
