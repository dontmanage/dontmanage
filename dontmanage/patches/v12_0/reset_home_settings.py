import dontmanage


def execute():
	dontmanage.reload_doc("core", "doctype", "user")
	dontmanage.db.sql(
		"""
		UPDATE `tabUser`
		SET `home_settings` = ''
		WHERE `user_type` = 'System User'
	"""
	)
