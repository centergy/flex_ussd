import time
import hashlib
import datetime
from collections import namedtuple

from django.core.cache import cache
from django.utils.functional import SimpleLazyObject

from .utils import AttributeBag
from .settings import ussd_settings
from .sessions import UssdSessionKey, UssdSession

_epoch = datetime.datetime(2017, 1, 1).timestamp()


class CacheBackend(object):

	session_class = UssdSession

	def get_session_key_class(self, request):
		return ussd_settings.SESSION_KEY_CLASS

	def get_session_class(self, request):
		return ussd_settings.SESSION_CLASS

	def get_session_timeout(self):
		return ussd_settings.SESSION_TIMEOUT

	# def get_screen_state_timeout(self):
	# 	return ussd_settings.SCREEN_STATE_TIMEOUT

	def get_request_sid(self, request):
		rv = request.GET.get('session_id')
		if not rv:
			rv = int((time.time() - _epoch) * 1000000)
		return rv

	def get_request_uid(self, request):
		return request.GET.get('msisdn', '0')

	def get_session_key(self, request):
		cls = self.get_session_key_class(request)
		return cls(uid=self.get_request_uid(request), sid=self.get_request_sid(request))

	# def get_screen_state_key(self, session):
	# 	return '%s/screen-state' % (session.key,)

	def create_new_session(self, key, request):
		cls = self.get_session_class(request)
		return cls(key)

	def get_saved_session(self, key, request):
		return cache.get(key.uid)

	def save_session(self, session, request):
		return cache.set(str(session.key.uid), session, self.get_session_timeout())

	def open_session(self, req):
		key = self.get_session_key(req)
		session = self.get_saved_session(key, req) or self.create_new_session(key, req)
		if session.key != key:
			session.restored = session.key
			session.key = key
		# session.key = key
		session.start_request(req)
		return session

	def close_session(self, session, request, response):
		session.finish_request(request)
		self.save_session(session, request)

	# def get_saved_screen_state(self, session):
	# 	return cache.get(self.get_screen_state_key(session))

	# def save_screen_state(self, state, session):
	# 	cache.set(self.get_screen_state_key(session), state, self.get_screen_state_timeout())

	# def expire_screen_state(self, session):
	# 	cache.delete(self.get_screen_state_key(session))


def _get_ussd_session_backend():
	cls = ussd_settings.SESSION_BACKEND
	return cls()


ussd_session_backend = SimpleLazyObject(_get_ussd_session_backend)