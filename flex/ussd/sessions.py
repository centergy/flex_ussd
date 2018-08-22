import datetime

from flex.datastructures.collections import AttrBag
from flex.utils.decorators import cached_property, export
from flex.utils.module_loading import import_if_string

from .abc import SessionManagerABC, AppBoundInstanceABC
from .wrappers import UssdRequest
from . import signals


@export
class SessionKey(object):

	__slots__ = ('phone_number', 'session_id')

	def __init__(self, phone_number, session_id=None):
		self.phone_number = phone_number
		self.session_id = session_id

	def __str__(self):
		return '%s/%s' % (self.phone_number, self.session_id)


@export
class Session(object):

	def __init__(self, key):
		self.key = key
		self.created_at = None
		self.accessed_at = None
		self.data = AttrBag()
		self.ctx = AttrBag()
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
		# if self._history is None:
		# 	self._history = History(self._history_stack, self.msisdn)
		return self._history

	@property
	def is_new(self):
		return self.accessed_at is None

	def _get_session_id(self):
		return self.key.session_id

	id = property(_get_session_id)
	sid = property(_get_session_id)
	session_id = property(_get_session_id)
	del _get_session_id

	def _get_msisdn(self):
		return self.key.phone_number

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
		return isinstance(other, Session) and self.key == other.key

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return hash(self.key)



@export
class SessionManager(AppBoundInstanceABC, SessionManagerABC):

	def __init__(self, app=None, backend=None, lifetime=60, timeout=None, name='ussd_session',
				session_class=Session, session_key_class=SessionKey):
		self.app = None
		self._session_timeout = None
		self.session_name = name
		self.session_lifetime = lifetime
		self.session_timeout = timeout

		self.set_backend(backend)
		self.session_class = import_if_string(session_class)
		self.session_key_class = import_if_string(session_key_class)

		if app is not None:
			self.init_app(app)

	@property
	def session_timeout(self):
		return self.session_lifetime if self._session_timeout is None else self._session_timeout

	@session_timeout.setter
	def session_timeout(self, value):
		self._session_timeout = value

	@property
	def backend(self):
		if self._backend is not None:
			return self._backend
		elif self.app is not None:
			return self.app.cache
		else:
			raise AttributeError(
				'Required attribute backend not configured for session manager %s.'\
				% (self.__class__.__name__,)
			)

	def set_backend(self, backend):
		if backend is not None:
			backend = import_if_string(backend)
			if callable(backend):
				backend = backend()
		self._backend = backend

	backend.setter(set_backend)

	@cached_property
	def stale_sessions(self):
		return self.session_timeout != self.session_lifetime

	def init_app(self, app):
		if self.app and app is not self.app:
			raise RuntimeError(
				'Error binding app %s to %s. Already bound to app %s'\
				% (app.name, self.__class__.__name__, self.app.name)
			)

		config = app.config.namespace('session_')

		self.app = app
		self.session_name = config.get('name', self.session_name)
		self.session_lifetime = config.get('lifetime', self.session_lifetime)
		self.session_timeout = config.get('timeout', self.session_timeout)

		self.session_class = import_if_string(config.get('class', self.session_class))
		self.session_key_class = import_if_string(config.get('key_class', self.session_key_class))

		if 'backend' in config:
			self.set_backend(config['backend'])

		self.backend

	def open(self, app, request):
		key = self.get_session_key(request)
		session = self.get_saved_session(key)
		if session and self.stale_sessions:
			session.is_stale = datetime.datetime.now() - self.session_lifetime > session.last_activity

		if not session:
			session = self.create_session(key)

		return session

	def close(self, app, session, response):
		self.saved_session(session)

	def create_session(self, key: SessionKey):
		return self.session_class(key)

	def get_session_key(self, request: UssdRequest):
		return self.session_key_class(request.phone_number, request.session_id)

	def get_backend_key(self, key: SessionKey):
		return '%s:%s' % (self.session_name, key.phone_number)

	def get_saved_session(self, key: SessionKey):
		return self.backend.get(self.get_backend_key(key))

	def saved_session(self, session):
		self.backend.set(self.get_backend_key(session.key), session, self.session_timeout)



class SessionMiddleware(object):

	__slots__ = ('handle_request',)

	def __init__(self, handle_request):
		self.handle_request = handle_request

	def __call__(self, app, request):
		session = app.session_manager.open(app, request)
		request.session = session = signals.open_session.pipe(app, session, request=request)

		response = self.handle_request(app, request)

		session = signals.save_session.pipe(app, session, response=response)
		app.session_manager.close(app, session, response)
		return response
