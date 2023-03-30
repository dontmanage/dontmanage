# Copyright (c) 2015, DontManage and Contributors
# License: MIT. See LICENSE

import dontmanage
import dontmanage.utils
from dontmanage import _
from dontmanage.auth import LoginManager
from dontmanage.integrations.doctype.ldap_settings.ldap_settings import LDAPSettings
from dontmanage.integrations.oauth2_logins import decoder_compat
from dontmanage.utils import cint
from dontmanage.utils.data import escape_html
from dontmanage.utils.html_utils import get_icon_html
from dontmanage.utils.jinja import guess_is_path
from dontmanage.utils.oauth import get_oauth2_authorize_url, get_oauth_keys, redirect_post_login
from dontmanage.utils.password import get_decrypted_password
from dontmanage.website.utils import get_home_page

no_cache = True


def get_context(context):
	redirect_to = dontmanage.local.request.args.get("redirect-to")

	if dontmanage.session.user != "Guest":
		if not redirect_to:
			if dontmanage.session.data.user_type == "Website User":
				redirect_to = get_home_page()
			else:
				redirect_to = "/app"

		if redirect_to != "login":
			dontmanage.local.flags.redirect_location = redirect_to
			raise dontmanage.Redirect

	context.no_header = True
	context.for_test = "login.html"
	context["title"] = "Login"
	context["provider_logins"] = []
	context["disable_signup"] = cint(dontmanage.get_website_settings("disable_signup"))
	context["disable_user_pass_login"] = cint(dontmanage.get_system_settings("disable_user_pass_login"))
	context["logo"] = dontmanage.get_website_settings("app_logo") or dontmanage.get_hooks("app_logo_url")[-1]
	context["app_name"] = (
		dontmanage.get_website_settings("app_name") or dontmanage.get_system_settings("app_name") or _("DontManage")
	)

	signup_form_template = dontmanage.get_hooks("signup_form_template")
	if signup_form_template and len(signup_form_template):
		path = signup_form_template[-1]
		if not guess_is_path(path):
			path = dontmanage.get_attr(signup_form_template[-1])()
	else:
		path = "dontmanage/templates/signup.html"

	if path:
		context["signup_form_template"] = dontmanage.get_template(path).render()

	providers = dontmanage.get_all(
		"Social Login Key",
		filters={"enable_social_login": 1},
		fields=["name", "client_id", "base_url", "provider_name", "icon"],
		order_by="name",
	)

	for provider in providers:
		client_secret = get_decrypted_password("Social Login Key", provider.name, "client_secret")
		if not client_secret:
			continue

		icon = None
		if provider.icon:
			if provider.provider_name == "Custom":
				icon = get_icon_html(provider.icon, small=True)
			else:
				icon = f"<img src={escape_html(provider.icon)!r} alt={escape_html(provider.provider_name)!r}>"

		if provider.client_id and provider.base_url and get_oauth_keys(provider.name):
			context.provider_logins.append(
				{
					"name": provider.name,
					"provider_name": provider.provider_name,
					"auth_url": get_oauth2_authorize_url(provider.name, redirect_to),
					"icon": icon,
				}
			)
			context["social_login"] = True

	context["ldap_settings"] = LDAPSettings.get_ldap_client_settings()

	login_label = [_("Email")]

	if dontmanage.utils.cint(dontmanage.get_system_settings("allow_login_using_mobile_number")):
		login_label.append(_("Mobile"))

	if dontmanage.utils.cint(dontmanage.get_system_settings("allow_login_using_user_name")):
		login_label.append(_("Username"))

	context["login_label"] = f" {_('or')} ".join(login_label)

	return context


@dontmanage.whitelist(allow_guest=True)
def login_via_token(login_token: str):
	sid = dontmanage.cache().get_value(f"login_token:{login_token}", expires=True)
	if not sid:
		dontmanage.respond_as_web_page(_("Invalid Request"), _("Invalid Login Token"), http_status_code=417)
		return

	dontmanage.local.form_dict.sid = sid
	dontmanage.local.login_manager = LoginManager()

	redirect_post_login(
		desk_user=dontmanage.db.get_value("User", dontmanage.session.user, "user_type") == "System User"
	)
