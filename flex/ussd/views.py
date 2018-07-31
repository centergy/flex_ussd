import io
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic import View
from django.core.cache import cache


from .settings import ussd_settings
from .screens import get_screen, ScreenState, UssdScreenType, CON, END, ScreenRef
from .utils import AttributeBag
from .utils.decorators import cached_property
from .backends import ussd_session_backend as backend
from .signals import ussd_screen_enter


from django.http import HttpResponse


class UssdView(View):
	"""docstring for ClassName"""

	@cached_property
	def buffer(self):
		return io.StringIO()

	def get_initial_screen(self):
		return ussd_settings.INITIAL_SCREEN

	def create_new_state(self, screen):
		screen = get_screen(screen)
		cls = screen.state_class
		return cls(screen._meta.name)

	def create_screen(self, state):
		cls = get_screen(state.screen)
		rv = cls(state)
		rv.session = self.session
		rv.request = self.request
		rv.argv = self.session.argv
		return rv

	def dispatch(self, request, *args, **kwargs):
		from time import time
		st = time()
		print('[VIEW START]')
		self.session = session = request.ussd_session

		if session.is_new:
			screen = self.get_initial_screen()
			state = session.state = self.create_new_state(screen)

			ussd_screen_enter.send(
					get_screen(screen),
					session=self.session
				)
		else:
			state = session.state

		if state is None:
			raise RuntimeError('Screen state cannot be None.')

		rv = self.dispatch_to_screen(state, *self.request.args)
		print('[VIEW END] time:', time()-st)
		return rv

	def dispatch_to_screen(self, state, *args):
		screen = self.create_screen(state)

		try:
			action = screen.dispatch(*args, restore=self.session.restored)
		except Exception as e:
			raise e

		if isinstance(action, ScreenRef):
			state = self.session.state = self.create_new_state(action.screen)
			if action.kwargs:
				state.update(action.kwargs)

			ussd_screen_enter.send(
					get_screen(action.screen),
					session=self.session
				)

			self.session.history.push(action)
			return self.dispatch_to_screen(state)

		if action in (CON, END):
			screen.teardown_state()
			return HttpResponse('%s %s' % (action, screen.payload))
		elif isinstance(action, str):
			screen.teardown_state()
			return HttpResponse(action)

		raise RuntimeError('Screen must return next action or ScreenRef.')






# CON, END, screen









