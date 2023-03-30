import dontmanage


def execute():
	dontmanage.db.sql(
		"""
		UPDATE `tabPrint Format`
		SET `print_format_type` = 'Jinja'
		WHERE `print_format_type` in ('Server', 'Client')
	"""
	)
	dontmanage.db.sql(
		"""
		UPDATE `tabPrint Format`
		SET `print_format_type` = 'JS'
		WHERE `print_format_type` = 'Js'
	"""
	)
