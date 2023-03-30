# Copyright (c) 2019, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class CommunicationLink(Document):
	pass


def on_doctype_update():
	dontmanage.db.add_index("Communication Link", ["link_doctype", "link_name"])
