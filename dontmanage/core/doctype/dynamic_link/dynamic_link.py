# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import dontmanage
from dontmanage.model.document import Document


class DynamicLink(Document):
	pass


def on_doctype_update():
	dontmanage.db.add_index("Dynamic Link", ["link_doctype", "link_name"])


def deduplicate_dynamic_links(doc):
	links, duplicate = [], False
	for l in doc.links or []:
		t = (l.link_doctype, l.link_name)
		if not t in links:
			links.append(t)
		else:
			duplicate = True

	if duplicate:
		doc.links = []
		for l in links:
			doc.append("links", dict(link_doctype=l[0], link_name=l[1]))
