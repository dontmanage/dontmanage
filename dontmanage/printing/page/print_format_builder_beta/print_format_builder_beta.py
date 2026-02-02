# Copyright (c) 2021, DontManage and Contributors
# MIT License. See license.txt


import functools

import dontmanage


@dontmanage.whitelist()
def get_google_fonts():
	return _get_google_fonts()


@functools.lru_cache
def _get_google_fonts():
	file_path = dontmanage.get_app_path("dontmanage", "data", "google_fonts.json")
	return dontmanage.parse_json(dontmanage.read_file(file_path))
