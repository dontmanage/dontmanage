import dontmanage

DONTMANAGE_CLOUD_DOMAINS = ("dontmanage.cloud", "dontmanageerp.com", "dontmanagehr.com", "dontmanage.dev")


def on_dontmanagecloud() -> bool:
	"""Returns true if running on DontManage Cloud.


	Useful for modifying few features for better UX."""
	return dontmanage.local.site.endswith(DONTMANAGE_CLOUD_DOMAINS)
