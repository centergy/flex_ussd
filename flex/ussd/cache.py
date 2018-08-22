from flex.utils.decorators import export
from flex.utils.module_loading import import_if_string


from .abc import CacheBackendABC


@export
class CacheBackend(CacheBackendABC):

	__slots__ = ('_store', 'key_prefix')

	def __init__(self, app=None, store=None, key_prefix=None):
		self.set_store(store)
		self.key_prefix = key_prefix
		if app is not None:
			self.init_app(app)

	@property
	def store(self):
		return self._store

	def set_store(self, store):
		if store is not None:
			store = import_if_string(store)
			if callable(store):
				store = store()
		self._store = store

	def init_app(self, app):
		config = app.config.namespace('cache_')

		key_prefix = config.get('key_prefix', self.key_prefix)
		self.key_prefix = '%s.%s' % (key_prefix, app.name) if key_prefix else '%s' % (app.name,)

		if 'store' in config:
			self.set_store(config['store'])

		if not self.store:
			raise AttributeError(
				'Required attribute store not configured for cache backend %s on app %s.'\
				% (self.__class__.__name__, app.name)
			)

	def make_key(self, key):
		return '%s%s%s' % (self.key_prefix, self.key_prefix and ':', key)

	def get(self, key):
		return self.store.get(self.make_key(key))

	def set(self, key, value, timeout=None):
		return self.store.set(self.make_key(key), value, timeout)

	def delete(self, key):
		return self.store.delete(self.make_key(key))

	def expire(self, key, timeout):
		return self.store.expire(self.make_key(key), timeout)


