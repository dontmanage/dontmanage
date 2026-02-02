import json

import dontmanage


def execute():
	if dontmanage.db.exists("Social Login Key", "github"):
		dontmanage.db.set_value(
			"Social Login Key", "github", "auth_url_data", json.dumps({"scope": "user:email"})
		)
