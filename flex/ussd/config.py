"""
Settings for USSD are all namespaced in the USSD setting.
For example your project's `settings.py` file might look like this:

USSD = {
	...
}

This module provides the `ussd_setting` object, that is used to access USSD
settings, checking for user settings first, then falling back to the defaults.
"""
from collections import MutableMapping

from flex.utils.decorators import export
from flex.datastructures.collections import AttrChainMap
from flex.utils.local import Proxy


@export
class ConfigAttribute(object):
	"""Makes an attribute forward to the config"""

	config_attr = 'config'

	def __init__(self, name, get_converter=None, config_attr=None):
		self.__name__ = name
		self.get_converter = get_converter
		self.config_attr = config_attr or self.config_attr

	def __get__(self, obj, type=None):
		if obj is None:
			return self
		rv = getattr(obj, self.config_attr)[self.__name__]
		if self.get_converter is not None:
			rv = self.get_converter(rv)
		return rv

	def __set__(self, obj, value):
		getattr(obj, self.config_attr)[self.__name__] = value


@export
class Config(AttrChainMap):
	"""Ussd global and application config."""

	__slots__ = ()

	def setdefaults(self, *mapping, **kwargs):
		"""Updates the config like :meth:`update` ignoring existing items.
		"""
		mappings = []
		if len(mapping) == 1:
			if hasattr(mapping[0], 'items'):
				mappings.append(mapping[0].items())
			else:
				mappings.append(mapping[0])
		elif len(mapping) > 1:
			raise TypeError(
				'expected at most 1 positional argument, got %d' % len(mapping)
			)
		mappings.append(kwargs.items())
		for mapping in mappings:
			for key, value in mapping:
				self.setdefault(key, value)

	def namespace(self, namespace, trim_namespace=True):
		"""Returns a Config object containing a subset of configuration options
		that match the specified namespace/prefix.
		"""
		return Config(self.get_namespace_view(namespace, trim_namespace))

	def get_namespace(self, namespace, trim_namespace=True):
		"""Returns a dictionary containing a subset of configuration options
		that match the specified namespace/prefix.
		"""
		return self.get_namespace_view(namespace, trim_namespace).copy()

	def get_namespace_view(self, namespace, trim_namespace=True):
		"""Returns a ConfigView of config options that match the specified
		namespace/prefix.
		"""
		return ConfigNamespaceView(self, _namespace_key_func(namespace, trim_namespace=trim_namespace))



def _namespace_key_func(namespace, trim_namespace=True):
	def make_key(key, reverse=False):
		if reverse:
			if trim_namespace:
				key = namespace + key
			return key

		if key.startswith(namespace):
			if trim_namespace:
				key = key[len(namespace):]
			return key

	return make_key



@export
class ConfigNamespaceView(MutableMapping):

	__slots__ = ('base', 'make_key',)

	def __init__(self, base, key_func):
		self.base = base
		self.make_key = key_func

	def __len__(self):
		return sum((1 for k in self))

	def __iter__(self):
		for key in self.base:
			yv = self.make_key(key)
			if yv is not None:
				yield yv

	def __bool__(self):
		return any(self)

	def __getitem__(self, key):
		return self.base[self.make_key(key, True)]

	def __setitem__(self, key, value):
		self.base[self.make_key(key, True)] = value

	def __delitem__(self, key):
		del self.base[self.make_key(key, True)]

	def __copy__(self):
		return dict(self.items())

	def copy(self):
		return self.__copy__()


@export
class UssdConfig(Config):
	__slots__ = ()

	def __init__(self, default_config=None):
		super(UssdConfig, self).__init__({}, Proxy(lambda: {}), default_config or {})

	def set_provider(self, provider):
		self.maps[-2:-1] = [Proxy(provider)]



ussd_config = UssdConfig()