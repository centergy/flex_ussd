import os
import re
import string
import random
import pickle
import warnings
from django.apps import apps
from collections import namedtuple
from django.conf import settings
from django.core.cache import cache
from collections import OrderedDict
from logging import getLogger

from ..datastructures import ClassReigistry, AttributeBag, choice, symbol
from ..utils.decorators import cached_property, class_property
from ..settings import ussd_settings

from .options import screen_meta_option, ScreenMetaOptions

logger = getLogger('ussd')


NOTHING = symbol('NOTHING')

_REGISTRY = ClassReigistry()

_UID_LEN = ussd_settings.SCREEN_UID_LEN


_UID_LOCK = set()
_UID_LOCK_FILE = os.path.join(settings.LOCAL_DATA_DIR, '.ussd-screens-uid.lock')
if os.path.exists(_UID_LOCK_FILE):
	with open(_UID_LOCK_FILE, 'r') as fo:
		_UID_LOCK = set((k.strip() for k in fo.read().split('\n') if k.strip()))


def _save_uid_lock():
	with open(_UID_LOCK_FILE, 'w+') as fo:
		fo.write('\n'.join(_UID_LOCK))


_UID_MAP =  ClassReigistry()
_UID_MAP_FILE = os.path.join(settings.LOCAL_DATA_DIR, '.ussd-screens-uid.map')
if os.path.exists(_UID_MAP_FILE):
	with open(_UID_MAP_FILE, 'rb') as mp:
		_UID_MAP = pickle.load(mp)


def _save_uid_map():
	with open(_UID_MAP_FILE, 'wb+') as fo:
		pickle.dump(_UID_MAP, fo)


def _generate_screen_uid():
	rv = None
	while rv is None or rv in _UID_LOCK or rv in _REGISTRY:
		rv = ''.join(random.choice(string.digits + string.ascii_lowercase)\
				for _ in range(2))
	_UID_LOCK.add(rv)
	_save_uid_lock()
	return rv



CON = 'CON'

END = 'END'


class ScreenRef(namedtuple('_ScreenRef', 'screen args kwargs')):
	__slots__ = ()


def render_screen(screen, *args, **kwargs):
	# if isinstance(screen, str):
	# 	screen = get_screen(screen)
	return ScreenRef(screen, args, kwargs)


def get_screen(screen, default=NOTHING):
	if isinstance(screen, UssdScreenType):
		return screen

	try:
		return _REGISTRY[screen]
	except KeyError:
		if default is NOTHING:
			raise LookupError('UssdScreen "%s" not found' % screen)
		else:
			return default


def get_screen_uid(screen, default=NOTHING):
	scls = get_screen(screen)
	rv = scls.__uid__
	assert rv in _UID_LOCK, ('Screen UID "%s" not registered' % (rv,))
	return rv


def get_home_screen():
	return ussd_settings.INITIAL_SCREEN




class ScreenState(AttributeBag):

	def __init__(self, screen, *bases, **data):
		super(ScreenState, self).__init__(*bases, **data)
		self.screen = screen

	def reset(self, *keep, **values):
		return super(ScreenState, self).reset('screen', *keep, **values)


class UssdScreenType(type):

	def __new__(mcls, name, bases, dct):
		super_new = super(UssdScreenType, mcls).__new__

		if not any((b for b in bases if isinstance(b, UssdScreenType))):
			return super_new(mcls, name, bases, dct)

		class Meta: pass
		dct.setdefault('Meta', Meta)

		cls = super_new(mcls, name, bases, dct)
		cls._set_meta_options()

		if not cls._meta.is_abstract:
			if cls._meta.slug in _REGISTRY:
				raise RuntimeError('UssdScreen name conflict. %s' % cls._meta.name)
			_REGISTRY[cls._meta.slug] = cls
			uid = _UID_MAP.get(cls._meta.slug)
			if not uid:
				uid = _generate_screen_uid()
				_UID_MAP[cls._meta.slug] = uid
				_save_uid_map()
			cls.__uid__ = uid
			_REGISTRY[uid] = cls

		return cls

	@property
	def _meta_options_cls(cls):
		rv = getattr(cls, '__meta_options_cls__', None)
		if rv is None:
			bases = []
			for c in cls.mro():
				oc = getattr(cls, 'META_OPTIONS_CLASS', None)
				if oc and not list(filter(lambda x: issubclass(x, oc), bases)):
					bases.append(oc)
			rv = type('%sMetaOptions' % cls.__name__, tuple(bases), {})
			setattr(cls, '__meta_options_cls__', rv)
		return rv

	def _set_meta_options(cls):
		meta = getattr(cls, 'Meta', None)
		base = getattr(cls, '_meta', None)
		cls._meta = cls._meta_options_cls(cls, meta, base)
		cls._meta._prepare()





# class UssdPageNav(object):
# 	"""docstring for UssdPageNav"""
# 	def __init__(self, arg):
# 		super(UssdPageNav, self).__init__()
# 		self.arg = arg



class UssdPayload(object):

	# __slots__ = '_body', '_header', '_footer', 'offset', 'max_len',

	def __init__(self):
		self.body = ''

	def append(self, *objs, sep=' ', end='\n'):
		# self.chunks.append('%s%s' % (sep.join((str(s) for s in objs)), end))
		self.body += '%s%s' % (sep.join((str(s) for s in objs)), end)

	def paginate(self, page_size, next_page_choice, prev_page_choice, foot=''):
		if isinstance(foot, (list, tuple)):
			foot_list = foot[:1]+[str(next_page_choice),]+foot[1:]
			foot = '\n'.join(foot)
		else:
			foot_list = None

		foot = foot and '\n%s' % foot
		lfoot = len(foot)
		if len(self.body.strip()) + lfoot <= page_size:
			yield self.body.strip()+foot
		else:
			lnext, lprev = len(str(next_page_choice)) + len('\n'), len(str(prev_page_choice))
			lnav = lnext + lprev
			chunk, i = self.body.strip(), 0
			while chunk:
				lc = len(chunk)
				if i > 0 and lc <= lprev + page_size:
					yield '%s\n%s' % (chunk, prev_page_choice)
					chunk = None
				else:
					yv = re.sub(r'([\n]+[^\n]+[\n]*)$', '', chunk[:(page_size-lnav if i > 0 else page_size-lfoot-lnext)]).strip()
					if i > 0:
						yield '%s\n%s\n%s' % (yv, prev_page_choice, next_page_choice)
					else:
						if foot_list:
							yield '%s\n%s' % (yv, '\n'.join(foot_list))
						else:
							yield '%s%s\n%s' % (yv, foot, next_page_choice)

					chunk = chunk[len(yv)+1:].strip()
				i += 1

	def __len__(self):
		return len(str(self))

	def __str__(self):
		# return ''.join(self.chunks).strip()
		return self.body.strip()

	# def __getstate__(self):
	# 	return self.chunks, None

	# def __setstate__(self, state):
	# 	self.chunks, self.prev = state




class UssdScreen(object, metaclass=UssdScreenType):

	META_OPTIONS_CLASS = ScreenMetaOptions

	CON = CON

	END = END

	state_class = ScreenState

	payload_class = UssdPayload

	lenargs = 1

	class ERRORS:
		LEN_ARGS = 'Invalid Choice'
		INVALID_CHOICE = 'Invalid Choice'


	class META:
		remember_session=False

	nav_menu = OrderedDict([
		('97', ("Previous", 1)),
		('99', ("Home", None)),
	])

	class PAGINATION_MENU:
		next = choice('98', 'More')
		prev = choice('0', 'Back')

	def __init__(self, state):
		self.state = state
		self.payload = self.create_payload()

	@class_property
	def name(cls):
		logger.warning('Property UssdScreen.name has been deprecated. '
			'Use %s._meta.name to get the name for %s.%s',
				cls.__name__, cls.__module__, cls.__name__
			)
		warnings.warn('Property UssdScreen.name has been deprecated. '
			'Use %s._meta.name to get the name for %s.%s' %
				(cls.__name__, cls.__module__, cls.__name__),
				stacklevel=3
			)
		return cls._meta.name

	@property
	def print(self):
		return self.payload.append

	def create_payload(self):
		return self.payload_class()

	def error(self, *objs, sep=' ', end='\n'):
		# self.print(getattr(self.ERRORS, code, code), *objs, sep=sep, end=end)
		self.print(*objs, sep=sep, end=end)
		return self.CON

	def render_lenargs_error(self, args):
		self.error(self.ERRORS.LEN_ARGS)

	def lenargs_error(self, args):
		self.render_lenargs_error(args)

	def check_lenargs(self, args):
		return self.lenargs >= len(args)

	# def get_nav_menu_str(self):
	# 	if not self.nav_menu:
	# 		return ''
	# 	return '\n'.join((('%s: %s' % (o, i[0])) for o,i in self.nav_menu.items()))

	def get_nav_menu_list(self):
		if not self.nav_menu:
			return []
		return list((('%s: %s' % (o, i[0])) for o,i in self.nav_menu.items()))

	def cancel_restoration(self, *args):
		self.session.reset()
		return render_screen(get_home_screen())

	def dispatch(self, *args, restore=False):
		if not self.check_lenargs(args):
			args = self.lenargs_error(args)
			if args and (args in (self.CON, self.END) or isinstance(args, ScreenRef)):
				return args

		if args and self.nav_menu and args[0] in self.nav_menu:
			if self.state.get('_current_page', 0) == 0:
				act = self.nav_menu[args[0]][1]
				if act is not None:
					act = self.session.history.pop(act)
				return render_screen(get_home_screen()) if act is None else act

		pg_menu = self.PAGINATION_MENU

		rv, pages, i = None, self.state.get('_pages', []), 0
		if args and args[0] in (pg_menu.next.value, pg_menu.prev.value) and len(pages) > 1:
			if args[0] == pg_menu.prev.value and self.state.get('_current_page', 0) > 0:
				self.state._current_page = i = self.state._current_page - 1
				rv = self.state._action
			elif args[0] == pg_menu.next.value and self.state.get('_current_page', 0) < len(pages)-1:
				self.state._current_page = i = self.state._current_page + 1
				rv = self.state._action

		if rv is None:
			if restore:
				if callable(getattr(self, 'restore', None)):
					rv = self.restore(*(args or ()))
				else:
					rv = self.cancel_restoration(*(args or ()))
			else:
				rv = self.render(*(args or ()))
			# rv = self.restore(*(args or ())) if restore else self.render(*(args or ()))
			if rv == self.CON or rv == self.END:
				self.state._action = rv
				self.state._pages = pages = list(
						self.payload.paginate(
								ussd_settings.MAX_PAGE_LENGTH-4,
								pg_menu.next, pg_menu.prev,
								self.get_nav_menu_list()
							)
						)
				self.state._current_page = i = 0
				# self.state._prev = self.payload
			else:
				return rv

		return '%s %s' % (rv, pages[i])
		# return '%s\n%s\n%s\n%s\n - Payload: %s\n - Page: %s\n - Response: %s'\
		# 	% (rv, '-'*40, self.state._prev, '-'*40, len(self.state._prev), len(pages[i]), len(rv))

	def render(self, *args):
		raise NotImplementedError('render method for screen %s' \
			% self.__class__.__name__)

	def teardown_state(self):
		# self.state._prev = self.response
		return self.state


