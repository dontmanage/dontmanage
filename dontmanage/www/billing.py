import dontmanage
from dontmanage.utils import cint

no_cache = 1


def get_context(context):
	dontmanage.db.commit()  # nosemgrep
	context = dontmanage._dict()
	context.boot = get_boot()
	return context


def get_boot():
	return dontmanage._dict(
		{
			"site_name": dontmanage.local.site,
			"read_only_mode": dontmanage.flags.read_only,
			"csrf_token": dontmanage.sessions.get_csrf_token(),
			"setup_complete": dontmanage.is_setup_complete(),
		}
	)
