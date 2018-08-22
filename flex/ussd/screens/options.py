import re
from threading import RLock
from flex.utils import text
from flex.utils.decorators import cached_class_property, export

from .. import exc
from ..namespaces import module_ussd_namespace


NOTHING = object()


@export
class screen_meta_option(object):

	__slots__ = ('__name__', 'option', 'fload', '_inherit', 'default', '__doc__', 'lock')

	def __init__(self, *opt, default=None, inherit=None, doc=None):
		self.fload = self.__name__ = self.option = None
		self.default = default
		self._inherit = inherit
		self.__doc__ = doc
		self.lock = RLock()

		lopt = len(opt)
		if lopt > 2:
			raise ValueError('expected at most 2 positional arg. got %d' % lopt)
		elif lopt == 1:
			assert isinstance(opt[0], str) or callable(opt[0]), (
					'Expected str and/or callable, got %s.' % type(opt[0])
				)
			if isinstance(opt[0], str):
				self.option = opt[0]
			else:
				self.loader(opt[0])
		elif lopt == 2:
			assert isinstance(opt[0], str) and callable(opt[1]), (
					'expected str and/or callable. got (%r, %r).'
					% (type(opt[0]), type(opt[1]))
				)
			self.option = opt[0]
			self.loader(opt[1])

	@property
	def name(self):
		return self.__name__

	@name.setter
	def name(self, value):
		self.__name__ = value
		if not self.option:
			self.option = value

	@property
	def inherit(self):
		return self._inherit is None or self._inherit

	def loader(self, fload):
		assert callable(fload), ('expected callable, got %s.' % type(fload))
		self.fload = fload
		self.__doc__ = self.__doc__ or fload.__doc__

	def getoption(self, value=None):
		if value is not None or self.default is None:
			return value
		elif callable(self.default):
			return self.default()
		else:
			return self.default

	def resolve(self, obj, value):
		base = getattr(obj, '_base', None)
		if self.fload is None:
			if value is None and self.inherit and base:
				value = getattr(base, self.name, None)
			return self.getoption(value)
		elif self.inherit:
			bv = base and getattr(base, self.name, None)
			return self.fload(obj, self.getoption(value), bv)
		else:
			return self.fload(obj, self.getoption(value))

	def setvalue(self, obj, value):
		obj.__dict__[self.name] = value

	def getvalue(self, obj, default=NOTHING):
		rv = obj.__dict__.get(self.name, default)
		if rv is NOTHING:
			raise AttributeError(self.name)
		return rv

	def load(self, obj, meta=None):
		# meta = getattr(obj, '_meta', None)
		self.__set__(obj, meta and getattr(meta, self.option, None))

	def __set__(self, obj, value):
		with self.lock:
			self.setvalue(obj, self.resolve(obj, value))

	def __get__(self, obj, cls):
		if obj is None:
			return self
		with self.lock:
			try:
				return self.getvalue(obj)
			except AttributeError:
				meta = getattr(obj, '_meta', None)
				rv = self.resolve(obj, meta and getattr(meta, self.option, None))
				self.setvalue(obj, rv)
				return rv

	def __call__(self, fload):
		assert self.fload is None, ('View option already has a loader.')
		self.loader(fload)
		return self



@export
class BaseScreenMetaOptions(object):

	def __init__(self, screen, meta, base=None):
		self.screen = screen
		self._meta = meta
		self._base = base

	@cached_class_property
	def _opts(cls):
		rv = {}
		for k in dir(cls):
			if k != '_opts' and k not in rv and isinstance(getattr(cls, k), screen_meta_option):
				rv[k] = getattr(cls, k)
				rv[k].name = k
		return rv

	def _prepare(self):
		assert hasattr(self, '_meta'), 'Screen meta options already prepared.'

		for k, opt in self._opts.items():
			opt.load(self, self._meta)

		del self._meta
		del self._base



@export
class ScreenMetaOptions(BaseScreenMetaOptions):

	is_abstract = screen_meta_option('abstract', default=False, inherit=False)

	@property
	def object_name(self):
		return self.screen.__name__

	@property
	def module(self):
		return self.screen.__module__

	@property
	def import_name(self):
		return '%s.%s' % (self.module, self.object_name)

	@screen_meta_option(inherit=False)
	def label(self, value):
		return value or self._make_screen_label()

	@screen_meta_option(inherit=False)
	def description(self, value):
		return value or self.screen.__doc__

	@screen_meta_option(inherit=False)
	def name(self, value):
		value = value or self._make_screen_name()

		if not re.search(r'^\.?[a-zA-Z0-9_][-a-zA-Z0-9_.]+\Z', value):
			raise exc.ScreenNameError(
				'Invalid UssdScreen name <%s(name="%s")>.' % (self.import_name, value)
			)

		if value[0] == '.':
			namespace = self._get_namespace()
			if namespace:
				value = namespace + value
			else:
				raise exc.ScreenNameError(
					'Screen <%s(name="%s")> has a relative name but it isn\'t in a '
					'registered namespace.' % (self.import_name, value)
				)
		return value

	def _get_namespace(self):
		return module_ussd_namespace(self.module)

	def _make_screen_name(self):
		return  '.%s' % text.snake(self.object_name)

	def _make_screen_label(self):
		return text.startcase(self.name.rpartition('.'))
