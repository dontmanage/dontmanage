import dontmanage


def execute():
	if "event_streaming" in dontmanage.get_installed_apps():
		return

	dontmanage.delete_doc_if_exists("Module Def", "Event Streaming", force=True)

	for doc in [
		"Event Consumer Document Type",
		"Document Type Mapping",
		"Event Producer",
		"Event Producer Last Update",
		"Event Producer Document Type",
		"Event Consumer",
		"Document Type Field Mapping",
		"Event Update Log",
		"Event Update Log Consumer",
		"Event Sync Log",
	]:
		dontmanage.delete_doc_if_exists("DocType", doc, force=True)
