import dontmanage
from dontmanage import _
from dontmanage.utils import cstr
from dontmanage.website.page_renderers.template_page import TemplatePage


class NotPermittedPage(TemplatePage):
	def __init__(self, path=None, http_status_code=None, exception=""):
		dontmanage.local.message = cstr(exception)
		super().__init__(path=path, http_status_code=http_status_code)
		self.http_status_code = 403

	def can_render(self):
		return True

	def render(self):
		action = f"/login?redirect-to={dontmanage.request.path}"
		if dontmanage.request.path.startswith("/app/") or dontmanage.request.path == "/app":
			action = "/login"
		dontmanage.local.message_title = _("Not Permitted")
		dontmanage.local.response["context"] = dict(
			indicator_color="red", primary_action=action, primary_label=_("Login"), fullpage=True
		)
		self.set_standard_path("message")
		return super().render()
