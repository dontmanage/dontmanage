import dontmanage
import dontmanage.www.list
from dontmanage import _

no_cache = 1


def get_context(context):
	if dontmanage.session.user == "Guest":
		dontmanage.throw(_("You need to be logged in to access this page"), dontmanage.PermissionError)

	active_tokens = dontmanage.get_all(
		"OAuth Bearer Token",
		filters=[["user", "=", dontmanage.session.user]],
		fields=["client"],
		distinct=True,
		order_by="creation",
	)

	client_apps = []

	for token in active_tokens:
		creation = get_first_login(token.client)
		app = {
			"name": token.get("client"),
			"app_name": dontmanage.db.get_value("OAuth Client", token.get("client"), "app_name"),
			"creation": creation,
		}
		client_apps.append(app)

	app = None
	if "app" in dontmanage.form_dict:
		app = dontmanage.get_doc("OAuth Client", dontmanage.form_dict.app)
		app = app.__dict__
		app["client_secret"] = None

	if app:
		context.app = app

	context.apps = client_apps


def get_first_login(client):
	login_date = dontmanage.get_all(
		"OAuth Bearer Token",
		filters=[["user", "=", dontmanage.session.user], ["client", "=", client]],
		fields=["creation"],
		order_by="creation",
		limit=1,
	)

	login_date = login_date[0].get("creation") if login_date and len(login_date) > 0 else None

	return login_date


@dontmanage.whitelist()
def delete_client(client_id):
	active_client_id_tokens = dontmanage.get_all(
		"OAuth Bearer Token", filters=[["user", "=", dontmanage.session.user], ["client", "=", client_id]]
	)
	for token in active_client_id_tokens:
		dontmanage.delete_doc("OAuth Bearer Token", token.get("name"), ignore_permissions=True)
