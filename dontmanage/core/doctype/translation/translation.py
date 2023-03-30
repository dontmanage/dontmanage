# Copyright (c) 2015, DontManage Technologies and contributors
# License: MIT. See LICENSE

import json

import dontmanage
from dontmanage.model.document import Document
from dontmanage.translate import MERGED_TRANSLATION_KEY, USER_TRANSLATION_KEY, get_translator_url
from dontmanage.utils import is_html, strip_html_tags


class Translation(Document):
	def validate(self):
		if is_html(self.source_text):
			self.remove_html_from_source()

	def remove_html_from_source(self):
		self.source_text = strip_html_tags(self.source_text).strip()

	def on_update(self):
		clear_user_translation_cache(self.language)

	def on_trash(self):
		clear_user_translation_cache(self.language)

	def contribute(self):
		pass

	def get_contribution_status(self):
		pass


@dontmanage.whitelist()
def create_translations(translation_map, language):
	from dontmanage.dontmanageclient import DontManageClient

	translation_map = json.loads(translation_map)
	translation_map_to_send = dontmanage._dict({})
	# first create / update local user translations
	for source_id, translation_dict in translation_map.items():
		translation_dict = dontmanage._dict(translation_dict)
		existing_doc_name = dontmanage.get_all(
			"Translation",
			{
				"source_text": translation_dict.source_text,
				"context": translation_dict.context or "",
				"language": language,
			},
		)
		translation_map_to_send[source_id] = translation_dict
		if existing_doc_name:
			dontmanage.db.set_value(
				"Translation",
				existing_doc_name[0].name,
				{
					"translated_text": translation_dict.translated_text,
					"contributed": 1,
					"contribution_status": "Pending",
				},
			)
			translation_map_to_send[source_id].name = existing_doc_name[0].name
		else:
			doc = dontmanage.get_doc(
				{
					"doctype": "Translation",
					"source_text": translation_dict.source_text,
					"contributed": 1,
					"contribution_status": "Pending",
					"translated_text": translation_dict.translated_text,
					"context": translation_dict.context,
					"language": language,
				}
			)
			doc.insert()
			translation_map_to_send[source_id].name = doc.name

	params = {
		"language": language,
		"contributor_email": dontmanage.session.user,
		"contributor_name": dontmanage.utils.get_fullname(dontmanage.session.user),
		"translation_map": json.dumps(translation_map_to_send),
	}

	translator = DontManageClient(get_translator_url())
	added_translations = translator.post_api("translator.api.add_translations", params=params)

	for local_docname, remote_docname in added_translations.items():
		dontmanage.db.set_value("Translation", local_docname, "contribution_docname", remote_docname)


def clear_user_translation_cache(lang):
	dontmanage.cache().hdel(USER_TRANSLATION_KEY, lang)
	dontmanage.cache().hdel(MERGED_TRANSLATION_KEY, lang)
