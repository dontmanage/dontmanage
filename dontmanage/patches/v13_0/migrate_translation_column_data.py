import dontmanage


def execute():
	dontmanage.reload_doctype("Translation")
	dontmanage.db.sql(
		"UPDATE `tabTranslation` SET `translated_text`=`target_name`, `source_text`=`source_name`, `contributed`=0"
	)
