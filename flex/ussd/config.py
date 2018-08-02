"""
Settings for USSD are all namespaced in the USSD setting.
For example your project's `settings.py` file might look like this:

USSD = {
	...
}

This module provides the `ussd_setting` object, that is used to access USSD
settings, checking for user settings first, then falling back to the defaults.
"""

from abc import ABCMeta, abstractmethod

from flex.utils.local import Proxy
from flex.utils.decorators import export
from flex.utils.module_loading import import_strings
from flex.datastructures.collections import AttrChainMap


__all__ = [
	'DEFAULT_CONFIG'
]

DEFAULT_CONFIG = dict(
	SESSION_BACKEND = 'ussd.backends.CacheBackend',
	SESSION_CLASS = 'ussd.sessions.UssdSession',
	SESSION_KEY_CLASS = 'ussd.sessions.UssdSessionKey',
	SESSION_KEY_PREFIX = 'ussd_session',
	SESSION_TIMEOUT = 120,
	URLS = (),
	DEFAULT_HTTP_METHODS = 'GET',
	INITIAL_SCREEN = None,
	SCREEN_STATE_TIMEOUT = 120,
	MAX_PAGE_LENGTH=182,
	SCREEN_UID_LEN=2,
	HISTORY_STATE_X = 16,

	DYNAMIC_SCREENS_BACKEND = None,
	NAMESPACE_LOADER = None,
)


# List of settings that may be in string import notation.
IMPORT_STRINGS = (
	'SESSION_BACKEND',
	'SESSION_CLASS',
	'SESSION_KEY_CLASS',
	'NAMESPACE_LOADER',
	'DYNAMIC_SCREENS_BACKEND',
)


VALUE_PARSERS = dict(
	URLS=lambda v: _normalize_urls(v),
	DEFAULT_HTTP_METHODS=lambda v: _ensure_list(v, str_split=True)
)


VALUE_CHECKS = dict(
	INITIAL_SCREEN=lambda v: v is not None,
)


@export
class ConfigProvider(metaclass=ABCMeta):
	__slots__ = ()

	@abstractmethod
	def get_config(self):
		pass


@export
class Config(AttrChainMap):
	"""The ussd config object.
	"""
	__slots__ = ('_provider',)

	_default_config = DEFAULT_CONFIG
	_import_strings = IMPORT_STRINGS
	_value_parsers = VALUE_PARSERS
	_value_checks = VALUE_CHECKS

	def __init__(self):
		object.__setattr__(self, '_provider', None)

	def __del__(self):
		pass

	def _get_current_object(self):
		"""Return the current config object from the provider.
		"""
		if self._provider is None:
			raise RuntimeError('USSD config provider not set.')
		return self._provider.get_config()

	def set_provider(self, provider: ConfigProvider):
		object.__setattr__(self, '_provider', provider)

	def init_config(self, config):
		for k, v in self._default_config.items():
			config.setdefault(k, v)

		for k, fn in self._value_parsers.items():
			config[k] = fn(config[k])

		for k, fn in self._value_checks.items():
			if not fn(config[k]):
				raise ValueError('Invalid USSD config. Key: %s.' % k)

		for k in self._import_strings:
			config[k] = import_strings(config[k])

		return config


config = Config()


def _ensure_list(val, str_split=None):
	if str_split is not None and isinstance(val, str):
		if str_split == True:
			return val.split()
		else:
			return val.split(str_split)

	if not isinstance(val, (tuple, list)):
		return [val]
	else:
		return list(val)



def _normalize_urls(urls):
	if not isinstance(urls, (tuple, list)):
		raise ValueError(
			'USSD.URLS setting value must be a list or tuple. %s given.'\
			% type(urls))

	defaults = dict(path=None, methods=config.DEFAULT_HTTP_METHODS)
	rv = []

	for url in urls:
		if isinstance(url, str):
			url = dict(path=url)

		if not isinstance(url, dict):
			raise ValueError('Items of USSD.URLS setting must be str or dict. %s given.' % type(url))

		for k,v in defaults.items():
			url.setdefault(k, v)

		if not url['path'] or not isinstance(url['path'], str):
			raise ValueError(
				'USSD.URLS[][\'path\'] setting must be str (regex pattern). %s given.'\
				% type(url['path'])
			)

		url['methods'] = _ensure_list(url['methods'], str_split=True)

		rv.append(url)
	return rv
