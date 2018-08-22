import re
from collections import namedtuple, OrderedDict
from logging import getLogger

from flex.datastructures.collections import AttrBag


from .options import ScreenMetaOptions
from .registry import registry

logger = getLogger('ussd')

NOTHING = object()

CON = 'CON'

END = 'END'



class choice(namedtuple('_choice', 'value label')):
	__slots__ = ()

	def as_str(self, template='%s: %s'):
		return template % self

	def __str__(self):
		return self.as_str()


class ScreenRef(namedtuple('_ScreenRef', 'screen args kwargs')):
	__slots__ = ()


def render_screen(screen, *args, **kwargs):
	return ScreenRef(screen, args, kwargs)


def get_screen(screen, default=NOTHING):
	if isinstance(screen, UssdScreenType):
		return screen
	try:
		return registry[screen]
	except KeyError:
		if default is NOTHING:
			raise LookupError('UssdScreen "%s" not found' % screen)
		else:
			return default




class ScreenState(AttrBag):

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
			if cls._meta.name in registry:
				raise RuntimeError('UssdScreen name conflict. %s' % cls._meta.name)
			registry[cls._meta.name] = cls

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
		cls._meta = cls._meta_options_cls(cls, getattr(cls, 'Meta', None), getattr(cls, '_meta', None))
		cls._meta._prepare()




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
		return render_screen(self.app.initial_screen)

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
				return render_screen(self.app.initial_screen) if act is None else act

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
								config.MAX_PAGE_LENGTH-4,
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


