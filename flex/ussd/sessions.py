import time
import hashlib
import datetime
from collections import namedtuple, ChainMap

from .datastructures import AttributeBag
from .config import config
from django.core.cache import cache
from django.utils import timezone
from .screens import ScreenRef, get_screen_uid, get_home_screen



_epoch = datetime.datetime(2017, 1, 1).timestamp()


class UssdSessionKey(namedtuple('_UssdSessionKey', 'uid sid')):

	__slots__ = ()

	@property
	def hash(self):
		return hashlib.sha256(str(self)).hexdigest()

	def __str__(self):
		return '%s:%s/%s' \
				% (config.SESSION_KEY_PREFIX, self.uid, self.sid)

	def asdict(self):
		return self._asdict()



class UssdSession(object):
	restored = None

	def __init__(self, key):
		self.key = key
		self.created_at = None
		self.accessed_at = None
		self.data = AttributeBag()
		self.ctx = AttributeBag()
		self.argv = None
		self._is_started = False
		self._history_stack = None
		self._history = None
		self.restored = None

	@property
	def context(self):
		return self.ctx

	@property
	def history(self):
		if self._history is None:
			self._history = History(self._history_stack, self.msisdn)
		return self._history

	@property
	def is_new(self):
		return self.accessed_at is None

	def _get_session_id(self):
		return self.key.sid

	id = property(_get_session_id)
	sid = property(_get_session_id)
	session_id = property(_get_session_id)
	del _get_session_id

	def _get_msisdn(self):
		return self.key.uid

	uid = property(_get_msisdn)
	msisdn = property(_get_msisdn)
	phone_number = property(_get_msisdn)
	del _get_msisdn

	def start_request(self, request):
		if getattr(self, '_is_started', False):
			return self
		if self.created_at is None:
			self.created_at = datetime.datetime.now()
		self._is_started = True

	def finish_request(self, request):
		self.accessed_at = datetime.datetime.now()

	def reset(self):
		self._history = None
		self._history_stack = []
		self.ctx.clear()
		self.data.clear()
		self.reset_restored()
		self.created_at = datetime.datetime.now()

	def reset_restored(self):
		self.restored = None

	def __getstate__(self):
		state = self.__dict__.copy()
		state['_history_stack'] = self.history.stack
		for k in ('_is_started', 'request', '_history'):
			if k in state:
				del state[k]
		state['_history'] = None
		state.setdefault('restored', None)
		return state

	def __eq__(self, other):
		return isinstance(other, UssdSession) and self.key == other.key

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.key)




class HistoryPath(str):
	"""A string-like object that has a head property
	"""
	__slots__ = ()

	@property
	def head(self):
		return self[-config.SCREEN_UID_LEN:]



class History(object):

	__slots__ = ('stack', 'key')

	def __init__(self, stack, key):
		self.stack = stack or []
		self.key = key

	@property
	def top(self):
		return

	def cache_key(self, path):
		return '%s:%s' % (self.key, path)

	def cache_timeout(self):
		return config.HISTORY_STATE_X * config.SESSION_TIMEOUT

	def pop(self, k=None):
		k = k or 1
		if self.stack and isinstance(k, int):
			k = -k
			self.stack[k:] = []
			path = self.stack and self.stack[-1] or None
			if path:
				ref = cache.get(self.cache_key(path))
				if ref is not None:
					return ScreenRef(path.head, *ref)

	def push(self, screen_ref):
		uid = get_screen_uid(screen_ref.screen)
		if not self.stack or self.stack[-1].head != uid:
			path = HistoryPath('%s/%s' % (self.stack and self.stack[-1] or '', uid))
			self.stack.append(path)
			cache.set(self.cache_key(path), screen_ref[1:], self.cache_timeout())



class SessionContext(ChainMap):

	def __init__(self, *maps):
		super(State, self).__init__(*maps)
		self.maps[0].setdefault('screen', None)
		self.maps[0].setdefault('argv', None)
		self.maps[0].setdefault('arg', None)

