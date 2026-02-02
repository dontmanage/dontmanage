import click

import dontmanage


def execute():
	dontmanage.delete_doc_if_exists("DocType", "Chat Message")
	dontmanage.delete_doc_if_exists("DocType", "Chat Message Attachment")
	dontmanage.delete_doc_if_exists("DocType", "Chat Profile")
	dontmanage.delete_doc_if_exists("DocType", "Chat Token")
	dontmanage.delete_doc_if_exists("DocType", "Chat Room User")
	dontmanage.delete_doc_if_exists("DocType", "Chat Room")
	dontmanage.delete_doc_if_exists("Module Def", "Chat")

	click.secho(
		"Chat Module is moved to a separate app and is removed from DontManage in version-13.\n"
		"Please install the app to continue using the chat feature: https://github.com/dontmanage/chat",
		fg="yellow",
	)
