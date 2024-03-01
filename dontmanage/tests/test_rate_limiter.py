# Copyright (c) 2020, DontManage and Contributors
# License: MIT. See LICENSE

import time

from werkzeug.wrappers import Response

import dontmanage
import dontmanage.rate_limiter
from dontmanage.rate_limiter import RateLimiter
from dontmanage.tests.utils import DontManageTestCase
from dontmanage.utils import cint


class TestRateLimiter(DontManageTestCase):
	def test_apply_with_limit(self):
		dontmanage.conf.rate_limit = {"window": 86400, "limit": 1}
		dontmanage.rate_limiter.apply()

		self.assertTrue(hasattr(dontmanage.local, "rate_limiter"))
		self.assertIsInstance(dontmanage.local.rate_limiter, RateLimiter)

		dontmanage.cache.delete(dontmanage.local.rate_limiter.key)
		delattr(dontmanage.local, "rate_limiter")

	def test_apply_without_limit(self):
		dontmanage.conf.rate_limit = None
		dontmanage.rate_limiter.apply()

		self.assertFalse(hasattr(dontmanage.local, "rate_limiter"))

	def test_respond_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		dontmanage.conf.rate_limit = {"window": 86400, "limit": 0.01}
		self.assertRaises(dontmanage.TooManyRequestsError, dontmanage.rate_limiter.apply)
		dontmanage.rate_limiter.update()

		response = dontmanage.rate_limiter.respond()

		self.assertIsInstance(response, Response)
		self.assertEqual(response.status_code, 429)

		headers = dontmanage.local.rate_limiter.headers()
		self.assertIn("Retry-After", headers)
		self.assertNotIn("X-RateLimit-Used", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertIn("X-RateLimit-Limit", headers)
		self.assertIn("X-RateLimit-Remaining", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"]) <= 86400)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 0)

		dontmanage.cache.delete(limiter.key)
		dontmanage.cache.delete(dontmanage.local.rate_limiter.key)
		delattr(dontmanage.local, "rate_limiter")

	def test_respond_under_limit(self):
		dontmanage.conf.rate_limit = {"window": 86400, "limit": 0.01}
		dontmanage.rate_limiter.apply()
		dontmanage.rate_limiter.update()
		response = dontmanage.rate_limiter.respond()
		self.assertEqual(response, None)

		dontmanage.cache.delete(dontmanage.local.rate_limiter.key)
		delattr(dontmanage.local, "rate_limiter")

	def test_headers_under_limit(self):
		dontmanage.conf.rate_limit = {"window": 86400, "limit": 0.01}
		dontmanage.rate_limiter.apply()
		dontmanage.rate_limiter.update()
		headers = dontmanage.local.rate_limiter.headers()
		self.assertNotIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"] < 86400))
		self.assertEqual(int(headers["X-RateLimit-Used"]), dontmanage.local.rate_limiter.duration)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 10000)

		dontmanage.cache.delete(dontmanage.local.rate_limiter.key)
		delattr(dontmanage.local, "rate_limiter")

	def test_reject_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.01, 86400)
		self.assertRaises(dontmanage.TooManyRequestsError, limiter.apply)

		dontmanage.cache.delete(limiter.key)

	def test_do_not_reject_under_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.02, 86400)
		self.assertEqual(limiter.apply(), None)

		dontmanage.cache.delete(limiter.key)

	def test_update_method(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		self.assertEqual(limiter.duration, cint(dontmanage.cache.get(limiter.key)))

		dontmanage.cache.delete(limiter.key)
