import json

import dontmanage


def execute():
	"""Handle introduction of UI tours"""
	completed = {}
	for tour in dontmanage.get_all("Form Tour", {"ui_tour": 1}, pluck="name"):
		completed[tour] = {"is_complete": True}

	User = dontmanage.qb.DocType("User")
	dontmanage.qb.update(User).set("onboarding_status", json.dumps(completed)).run()
