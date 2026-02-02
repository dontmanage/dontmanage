import dontmanage
from dontmanage.modules import load_doctype_module
from dontmanage.website.page_renderers.template_page import TemplatePage


class ListPage(TemplatePage):
	def can_render(self):
		doctype = self.path
		if not doctype or doctype == "Web Page":
			return False

		try:
			meta = dontmanage.get_meta(doctype)
		except dontmanage.DoesNotExistError:
			dontmanage.clear_last_message()
			return False

		if meta.has_web_view:
			return True

		if meta.custom:
			return False

		module = load_doctype_module(doctype)
		return hasattr(module, "get_list_context")

	def render(self):
		dontmanage.form_dict.doctype = self.path
		self.set_standard_path("portal")
		return super().render()
