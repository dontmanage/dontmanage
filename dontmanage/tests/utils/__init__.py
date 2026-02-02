import logging
import os
from functools import wraps

import dontmanage

logger = logging.Logger(__file__)

from .generators import *


def whitelist_for_tests(**whitelist_kwargs):
	"""Decorator to whitelist test endpoints.

	Only allows access when running in test mode or running a development server with testing enabled.
	Supports all parameters that @dontmanage.whitelist() accepts.

	Usage:
		@whitelist_for_tests(allow_guest=True)
		def my_guest_test_endpoint():
			...
	"""

	def decorator(fn):
		@wraps(fn)
		def wrapper(*args, **kwargs):
			if not (
				dontmanage.in_test or (dontmanage._dev_server and dontmanage.conf.allow_tests) or os.environ.get("CI")
			):
				dontmanage.throw(  # nosemgrep: dontmanage-missing-translate-function-python
					'Test endpoints are only available when running in test mode or running a development server ("bench start") with the "allow_tests" site config enabled'
				)
			return fn(*args, **kwargs)

		return dontmanage.whitelist(**whitelist_kwargs)(wrapper)

	return decorator


def check_orpahned_doctypes():
	"""Check that all doctypes in DB actually exist after patch test"""
	from dontmanage.model.base_document import get_controller

	doctypes = dontmanage.get_all("DocType", {"custom": 0}, pluck="name")
	orpahned_doctypes = []

	for doctype in doctypes:
		try:
			get_controller(doctype)
		except ImportError:
			orpahned_doctypes.append(doctype)

	if orpahned_doctypes:
		dontmanage.throw(
			"Following doctypes exist in DB without controller.\n {}".format("\n".join(orpahned_doctypes))
		)


def toggle_test_mode(enable: bool):
	"""Enable or disable `dontmanage.in_test` (and related deprecated flag)"""
	dontmanage.in_test = enable
	dontmanage.local.flags.in_test = enable


from dontmanage.deprecation_dumpster import (
	get_tests_CompatDontManageTestCase,
)
from dontmanage.deprecation_dumpster import (
	tests_change_settings as change_settings,
)
from dontmanage.deprecation_dumpster import (
	tests_debug_on as debug_on,
)

DontManageTestCase = get_tests_CompatDontManageTestCase()

from dontmanage.deprecation_dumpster import (
	tests_patch_hooks as patch_hooks,
)
from dontmanage.deprecation_dumpster import (
	tests_timeout as timeout,
)
from dontmanage.deprecation_dumpster import (
	tests_utils_get_dependencies as get_dependencies,
)
