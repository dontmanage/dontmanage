# Copyright (c) 2017, DontManage and Contributors
# License: MIT. See LICENSE
import dontmanage


@dontmanage.whitelist()
def get_leaderboard_config():
	leaderboard_config = dontmanage._dict()
	leaderboard_hooks = dontmanage.get_hooks("leaderboards")
	for hook in leaderboard_hooks:
		leaderboard_config.update(dontmanage.get_attr(hook)())

	return leaderboard_config
