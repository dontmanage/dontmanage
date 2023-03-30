# imports - standard imports
import sys

# imports - module imports
from dontmanage.integrations.dontmanage_providers.dontmanagecloud import dontmanagecloud_migrator


def migrate_to(local_site, dontmanage_provider):
	if dontmanage_provider in ("dontmanage.cloud", "dontmanagecloud.com"):
		return dontmanagecloud_migrator(local_site)
	else:
		print(f"{dontmanage_provider} is not supported yet")
		sys.exit(1)
