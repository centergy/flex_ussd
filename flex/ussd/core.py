from collections import OrderedDict

from flex.utils.decorators import cached_property
from flex.utils.module_loading import import_if_string, import_strings

from .config import Config, ConfigAttribute, ussd_config
from .wrappers import UssdCode
from .exc import ImproperlyConfigured
from . import signals


class UssdApp(object):

	config_class = Config

	name = ConfigAttribute('name')
	inital_screen = ConfigAttribute('inital_screen')

	default_config = dict(
		cache_backend='flex.ussd.cache.CacheBackend',
		session_manager='flex.ussd.sessions.SessionManager',
		middleware=[]
	)

	def __init__(self, name, *, inital_screen=None, **config):
		self.config = self.make_config(config)
		self.name = name
		self.inital_screen = inital_screen

	@cached_property
	def cache(self):
		return self._create_cache_backend()

	@cached_property
	def session_manager(self):
		return self._create_session_manager()

	@cached_property
	def handler(self):
		return self._create_request_handler()

	@cached_property
	def middleware(self):
		rv = list(self.config.get('global_middleware', []))
		rv.extend(self.config.get('middleware', []))
		# rv = signals.middleware_list.pipe(self, rv)
		return import_strings(rv)

	def make_config(self, config=None):
		return self.config_class(config or {}, self.default_config, ussd_config)

	def _create_cache_backend(self):
		factory = signals.cache_backend_factory.pipe(self, self.config.get('cache_backend'))
		factory = import_if_string(factory)

		if not callable(factory):
			raise ImproperlyConfigured('Cache backend must be a type or callable. In app %s.' % self.name)

		return factory(self)

	def _create_session_manager(self):
		factory = signals.session_manager_factory.pipe(self, self.config.get('session_manager'))
		factory = import_if_string(factory)

		if not callable(factory):
			raise ImproperlyConfigured('Session manager must be a type or callable. In app %s.' % self.name)

		return factory(self)

	def _create_request_handler(self):
		factory = signals.request_handler_factory.pipe(self, self.config.get('request_handler'))
		factory = import_if_string(factory)

		if not callable(factory):
			raise ImproperlyConfigured('Request handler must be a type or callable. In app %s.' % self.name)

		return factory(self)



class UssdAppRouter(object):
	__slots__ = ('routes', 'base_code')

	def __init__(self, code=None):
		self.routes = OrderedDict()
		self.base_code = code and UssdCode(code)

	def route(self, code, handler):
		code = code if isinstance(code, UssdCode) else UssdCode(code)
		key_code = tuple(code)
		if key_code in self.routes:
			raise ValueError('Ussd code %s already registered in ussd router.' % (code,))
		self.routes[key_code] = (code, handler)

	def resolve(self, request):


		ussd_string = request.ussd_string
		if ussd_string.startswith(self.base_code):
			ussd_string = ussd_string[len(self.base_code):]
			codes = sorted(filter(ussd_string.startswith, self.routes.keys()))
			if codes:
				code = codes[-1]
				route_code = '%s*%s' % (self.base_code, code) if self.base_code else code
				request.route_code = route_code
				return self.routes[code], route_code
		return None, None

	def __len__(self):
		return self.routes.__len__()

	def __contains__(self, code):
		return self.routes.__contains__(code)




apps = dict()