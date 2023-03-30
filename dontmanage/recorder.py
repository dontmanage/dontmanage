# Copyright (c) 2018, DontManage and Contributors
# License: MIT. See LICENSE
import datetime
import functools
import inspect
import json
import re
import time
from collections import Counter
from typing import Callable

import sqlparse

import dontmanage
from dontmanage import _
from dontmanage.database.database import is_query_type

RECORDER_INTERCEPT_FLAG = "recorder-intercept"
RECORDER_REQUEST_SPARSE_HASH = "recorder-requests-sparse"
RECORDER_REQUEST_HASH = "recorder-requests"
TRACEBACK_PATH_PATTERN = re.compile(".*/apps/")


def sql(*args, **kwargs):
	start_time = time.time()
	result = dontmanage.db._sql(*args, **kwargs)
	end_time = time.time()

	stack = list(get_current_stack_frames())
	query = sqlparse.format(str(dontmanage.db.last_query).strip(), keyword_case="upper", reindent=True)

	# Collect EXPLAIN for executed query
	if is_query_type(query, ("select", "update", "delete")):
		# Only SELECT/UPDATE/DELETE queries can be "EXPLAIN"ed
		explain_result = dontmanage.db._sql(f"EXPLAIN {query}", as_dict=True)
	else:
		explain_result = []

	data = {
		"query": query,
		"stack": stack,
		"explain_result": explain_result,
		"time": start_time,
		"duration": float(f"{(end_time - start_time) * 1000:.3f}"),
	}

	dontmanage.local._recorder.register(data)
	return result


def get_current_stack_frames():
	try:
		current = inspect.currentframe()
		frames = inspect.getouterframes(current, context=10)
		for frame, filename, lineno, function, context, index in list(reversed(frames))[:-2]:
			if "/apps/" in filename:
				yield {
					"filename": TRACEBACK_PATH_PATTERN.sub("", filename),
					"lineno": lineno,
					"function": function,
				}
	except Exception:
		pass


def record(force=False):
	if __debug__:
		if dontmanage.cache().get_value(RECORDER_INTERCEPT_FLAG) or force:
			dontmanage.local._recorder = Recorder()


def dump():
	if __debug__:
		if hasattr(dontmanage.local, "_recorder"):
			dontmanage.local._recorder.dump()


class Recorder:
	def __init__(self):
		self.uuid = dontmanage.generate_hash(length=10)
		self.time = datetime.datetime.now()
		self.calls = []
		if dontmanage.request:
			self.path = dontmanage.request.path
			self.cmd = dontmanage.local.form_dict.cmd or ""
			self.method = dontmanage.request.method
			self.headers = dict(dontmanage.local.request.headers)
			self.form_dict = dontmanage.local.form_dict
		else:
			self.path = None
			self.cmd = None
			self.method = None
			self.headers = None
			self.form_dict = None

		_patch()

	def register(self, data):
		self.calls.append(data)

	def dump(self):
		request_data = {
			"uuid": self.uuid,
			"path": self.path,
			"cmd": self.cmd,
			"time": self.time,
			"queries": len(self.calls),
			"time_queries": float("{:0.3f}".format(sum(call["duration"] for call in self.calls))),
			"duration": float(f"{(datetime.datetime.now() - self.time).total_seconds() * 1000:0.3f}"),
			"method": self.method,
		}
		dontmanage.cache().hset(RECORDER_REQUEST_SPARSE_HASH, self.uuid, request_data)
		dontmanage.publish_realtime(
			event="recorder-dump-event",
			message=json.dumps(request_data, default=str),
			user="Administrator",
		)

		self.mark_duplicates()

		request_data["calls"] = self.calls
		request_data["headers"] = self.headers
		request_data["form_dict"] = self.form_dict
		dontmanage.cache().hset(RECORDER_REQUEST_HASH, self.uuid, request_data)

	def mark_duplicates(self):
		counts = Counter([call["query"] for call in self.calls])
		for index, call in enumerate(self.calls):
			call["index"] = index
			call["exact_copies"] = counts[call["query"]]


def _patch():
	dontmanage.db._sql = dontmanage.db.sql
	dontmanage.db.sql = sql


def _unpatch():
	dontmanage.db.sql = dontmanage.db._sql


def do_not_record(function):
	def wrapper(*args, **kwargs):
		if hasattr(dontmanage.local, "_recorder"):
			del dontmanage.local._recorder
			dontmanage.db.sql = dontmanage.db._sql
		return function(*args, **kwargs)

	return wrapper


def administrator_only(function):
	def wrapper(*args, **kwargs):
		if dontmanage.session.user != "Administrator":
			dontmanage.throw(_("Only Administrator is allowed to use Recorder"))
		return function(*args, **kwargs)

	return wrapper


@dontmanage.whitelist()
@do_not_record
@administrator_only
def status(*args, **kwargs):
	return bool(dontmanage.cache().get_value(RECORDER_INTERCEPT_FLAG))


@dontmanage.whitelist()
@do_not_record
@administrator_only
def start(*args, **kwargs):
	dontmanage.cache().set_value(RECORDER_INTERCEPT_FLAG, 1)


@dontmanage.whitelist()
@do_not_record
@administrator_only
def stop(*args, **kwargs):
	dontmanage.cache().delete_value(RECORDER_INTERCEPT_FLAG)


@dontmanage.whitelist()
@do_not_record
@administrator_only
def get(uuid=None, *args, **kwargs):
	if uuid:
		result = dontmanage.cache().hget(RECORDER_REQUEST_HASH, uuid)
	else:
		result = list(dontmanage.cache().hgetall(RECORDER_REQUEST_SPARSE_HASH).values())
	return result


@dontmanage.whitelist()
@do_not_record
@administrator_only
def export_data(*args, **kwargs):
	return list(dontmanage.cache().hgetall(RECORDER_REQUEST_HASH).values())


@dontmanage.whitelist()
@do_not_record
@administrator_only
def delete(*args, **kwargs):
	dontmanage.cache().delete_value(RECORDER_REQUEST_SPARSE_HASH)
	dontmanage.cache().delete_value(RECORDER_REQUEST_HASH)


def record_queries(func: Callable):
	"""Decorator to profile a specific function using recorder."""

	@functools.wraps(func)
	def wrapped(*args, **kwargs):
		record(force=True)
		dontmanage.local._recorder.path = f"Function call: {func.__module__}.{func.__qualname__}"
		ret = func(*args, **kwargs)
		dump()
		_unpatch()
		print("Recorded queries, open recorder to view them.")
		return ret

	return wrapped
