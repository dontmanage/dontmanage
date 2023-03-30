# Copyright (c) 2020, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage import _
from dontmanage.model.document import Document


class OnboardingStep(Document):
	def before_export(self, doc):
		doc.is_complete = 0
		doc.is_skipped = 0


@dontmanage.whitelist()
def get_onboarding_steps(ob_steps):
	steps = []
	for s in json.loads(ob_steps):
		doc = dontmanage.get_doc("Onboarding Step", s.get("step"))
		step = doc.as_dict().copy()
		step.label = _(doc.title)
		if step.action == "Create Entry":
			step.is_submittable = dontmanage.db.get_value(
				"DocType", step.reference_document, "is_submittable", cache=True
			)
		steps.append(step)

	return steps
