import re
from collections import OrderedDict, namedtuple, Mapping

from . void import Void, VoidType
from . symbol import symbol


NOTHING = symbol('NOTHING')




class choice(namedtuple('_choice', 'value label')):
	__slots__ = ()

	def as_str(self, template='%s: %s'):
		return template % self

	def __str__(self):
		return self.as_str()



class ClassReigistry(OrderedDict):
	pass


class AttributeBag(object):

	def __init__(self, *bases, **data):
		self._bases = list(bases)
		for k,v in data.items():
			setattr(self, k, v)

	def get(self, name, default=None):
		return getattr(self, name, default)

	def pop(self, name, default=NOTHING):
		if default is NOTHING:
			return self.__dict__.pop(name)
		else:
			return self.__dict__.pop(name, default)

	def setdefault(self, name, default=None):
		return self.__dict__.setdefault(name, default)

	def setdefaults(self, *args, **kwargs):
		arg = args and args[0]
		if len(args) > 1:
			raise ValueError(
				'Expected at most 1 positional argument. Got %s' % len(args)
			)

		if arg:
			if not isinstance(arg, Mapping):
				raise TypeError('Mapping expected. Got %s' % type(arg))
			arg.update(kwargs)
		else:
			arg = kwargs

		for k, v in arg.items():
			self.setdefault(k, v)

	def update(self, *args, **kwargs):
		self.__dict__.update(*args, **kwargs)

	def todict(self):
		return dict(self.__dict__)

	def getkeys(self):
		return self.__dict__.keys()

	def getvalues(self):
		return self.__dict__.values()

	def getitems(self):
		return self.__dict__.items()

	def copy(self, **new_values):
		rv = self.__class__(self.__dict__)
		if new_values:
			rv.update(new_values)
		return rv

	def clear(self):
		return self.__dict__.clear()

	def reset(self, *keep, **values):
		for k in keep:
			if k in self:
				values.setdefault(k, getattr(self, k))
		self.clear()
		self.update(values)

	def __contains__(self, item):
		if item in self.__dict__:
			return True
		for base in self._bases:
			if item in base:
				return True
		return False

	# def __len__(self):
	# 	return len(self.__dict__)

	def __iter__(self):
		return iter(self.getitems())

	def __getitem__(self, key):
		try:
			return getattr(self, key)
		except AttributeError:
			raise KeyError(key)

	def __setitem__(self, key, value):
		setattr(self, key, value)

	def __delitem__(self, key):
		try:
			delattr(self, key)
		except AttributeError:
			raise KeyError(key)

	def __getattr__(self, name):
		if name == '_bases':
			self._bases = rv = []
			return rv

		rv = NOTHING
		for base in self._bases:
			rv = getattr(base, name, NOTHING)
			if rv is not NOTHING:
				return rv

		if rv is NOTHING:
			raise AttributeError('%s has no attribute "%s".'\
				% (self.__class__.__name__, name))

	def __getstate__(self):
		rv = self.__dict__.copy()
		rv.setdefault('_bases', self._bases)
		return rv

	def __str__(self):
		return '%s' % self.__dict__

	def __repr__(self):
		return '<%s: %s>' % (self.__class__.__name__, self)



# class LazyList(object):
# 	__slot__ = ('src','items')

# 	def __init__(self, items):
# 		self.items = items

# 	@property
# 	def function(self):
# 		pass

# 	def __iter__(self):
# 		if isinstance(self.items, list):
# 			return iter(self.items)

# 		items = []
# 		for i in self.items:
# 			yield i
# 			items.append(i)
# 		self.items = items





class PushList(list):

	def push(self, *items):
		self.extend(list(items))



_ussd_split_re = r'\*(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)'

def split_argstr(s):
	return re.split(_ussd_split_re, s) if s else []


class ArgumentVector(list):

	__slots__ = ()

	def __init__(self, service_code=None, argstr='', base_code=None):
		if base_code and argstr and argstr.startswith(base_code):
			argstr = argstr[len(base_code):].lstrip('*')
			if service_code:
				service_code = '*'.join((service_code, base_code))

		super(ArgumentVector, self).__init__(
			(s.replace('"', '') for s in split_argstr(argstr))
		)
		if service_code:
			self.insert(0, service_code)

	@property
	def service_code(self):
		return self[0].split('*', 1)[0]

	@property
	def base_code(self):
		if '*' in self[0]:
			return self[0].split('*', 1)[1]
		else:
			return ''

	@property
	def top(self):
		return self[-1] if len(self) > 1 else None

	def __sub__(self, other):
		if not isinstance(other, ArgumentVector):
			return NotImplemented

		ld = len(self) - len(other)
		return self[-ld:] if ld > 0 else []

	def __str__(self):
		return '%s' % '*'.join(self)

	def __repr__(self):
		return '<ArgumentVector: %s>' % (self,)
