import json

import dontmanage


@dontmanage.whitelist()
def get_onboarding_status():
	onboarding_status = dontmanage.db.get_value("User", dontmanage.session.user, "onboarding_status")
	return dontmanage.parse_json(onboarding_status) if onboarding_status else {}


@dontmanage.whitelist()
def update_user_onboarding_status(steps: str, appName: str):
	steps = json.loads(steps)

	# get the current onboarding status
	onboarding_status = dontmanage.db.get_value("User", dontmanage.session.user, "onboarding_status")
	onboarding_status = dontmanage.parse_json(onboarding_status)

	# update the onboarding status
	onboarding_status[appName + "_onboarding_status"] = steps

	dontmanage.db.set_value(
		"User", dontmanage.session.user, "onboarding_status", json.dumps(onboarding_status), update_modified=False
	)
