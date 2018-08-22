from functools import wraps
from flex.utils.decorators import cached_property
from flex.utils.module_loading import import_if_string, import_strings

from .abc import AppBoundInstanceABC
from .wrappers import UssdRequest, UssdResponse, UssdStatus
from .screens import get_screen, ScreenRef
from . import signals


class RequestHandler(AppBoundInstanceABC):

	def __init__(self, app=None):
		self.app = None
		self._exception_middleware = []
		if app is not None:
			self.init_app(app)

	@cached_property
	def middleware_chain(self):
		return self.create_middleware_chain()

	def init_app(self, app):
		if self.app and app is not self.app:
			raise RuntimeError(
				'Error binding app %s to %s. Already bound to %s'\
				% (app.name, self.__class__.__name__, self.app.name)
			)
		self.app = app

	def create_middleware_chain(self):
		self._exception_middleware = []
		handler = self.wrap_exception_handler(self.dispatch_request, self.get_exception_handler(0))
		for mware in self.app.middleware:
			mw_instance = mware(handler)
			if mw_instance is not None:
				if hasattr(mw_instance, 'process_exception'):
					self._exception_middleware.append(mw_instance.process_exception)

				handler = self.wrap_exception_handler(
					mw_instance,
					self.get_exception_handler(len(self._exception_middleware))
				)
		return handler

	def before_request(self, request):
		request.app = self.app
		signals.before_request.send(self.app, request=request)
		return request

	def after_request(self, response, request):
		signals.after_request.send(self.app, response=response, request=request)
		return response

	def full_dispatch_request(self, request):
		self.before_request(request)

		response = self.middleware_chain(self.app, request)

		self.after_request(response, request)
		return response

	def create_new_state(self, screen):
		screen = get_screen(screen)
		cls = screen.state_class
		return cls(screen._meta.name)

	def create_screen(self, state, request):
		cls = get_screen(state.screen)
		rv = cls(state)
		rv.app = self.app
		rv.request = request
		rv.session = request.session
		rv.argv = request.session.argv
		return rv

	def dispatch_request(self, app, request):
		session = request.session

		if session.is_new:
			screen = self.app.initial_screen
			state = session.state = self.create_new_state(screen)
		else:
			state = session.state

		if state is None:
			raise RuntimeError('Screen state cannot be None.')

		rv = self.dispatch_to_screen(state, request)
		return rv

	def dispatch_to_screen(self, state, request, *args):
		screen = self.create_screen(state, request)

		try:
			response = screen.dispatch(*args, restore=request.session.is_stale)
		except Exception as e:
			raise e

		if isinstance(response, ScreenRef):
			state = request.session.state = self.create_new_state(response.screen)
			if response.kwargs:
				state.update(response.kwargs)

			request.session.history.push(response)
			return self.dispatch_to_screen(state, request)

		if isinstance(response, UssdResponse):
			return response
		elif isinstance(response, tuple):
			return UssdResponse(*response)
		elif isinstance(response, str):
			return UssdResponse(response)

		raise RuntimeError('Screen must return next action or ScreenRef.')

	def wrap_exception_handler(self, func, exception_handler=None):
		"""Wrap the given callable in exception-to-response conversion.
		"""
		exception_handler = exception_handler or self.get_exception_response
		@wraps(func)
		def inner(app, request):
			try:
				response = func(app, request)
			except Exception as exc:
				response = exception_handler(app, request, exc)
			return response
		return inner

	def get_exception_handler(self, depth=0):
		def exception_handler(app, request, exception):
			for handler in self._exception_middleware[depth:]:
				response = handler(app, request, exception)
				if response:
					return response
			return self.get_exception_response(app, request, exception)
		return exception_handler

	def get_exception_response(self, app, request, exc):
		raise exc

	def __call__(self, request):
		return self.full_dispatch_request(request)






