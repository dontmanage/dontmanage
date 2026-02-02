import dontmanage


def execute():
	"""
	Deprecate Feedback Trigger and Rating. This feature was not customizable.
	Now can be achieved via custom Web Forms
	"""
	dontmanage.delete_doc("DocType", "Feedback Trigger")
	dontmanage.delete_doc("DocType", "Feedback Rating")
