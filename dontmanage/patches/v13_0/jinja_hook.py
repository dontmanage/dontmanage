# Copyright (c) 2021, DontManage and Contributors
# License: MIT. See LICENSE

from click import secho

import dontmanage


def execute():
	if dontmanage.get_hooks("jenv"):
		print()
		secho(
			'WARNING: The hook "jenv" is deprecated. Follow the migration guide to use the new "jinja" hook.',
			fg="yellow",
		)
		secho("https://github.com/dontmanage/dontmanage/wiki/Migrating-to-Version-13", fg="yellow")
		print()
