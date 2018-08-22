from . import signals
from .core import UssdRouter



class UssdView(object):
	"""A simple ussd view"""

	ussd_apps = [

	]

	def match_ussd_app(self, request):
		apps = list(filter(lambda k: request.ussd_string.startswith(k[0]), self.ussd_apps))
		apps and apps.sort(key=lambda x: x[0])
		if not apps:
			raise RuntimeError('Error matching ussd app.')
		return apps[-1]

	def make_ussd_request(self, http_request):
		raise NotImplementedError('make_ussd_request')

	def process_ussd_request(self, ussd_app, ussd_request):
		return

	def process_ussd_response(self, ussd_app, ussd_response):
		return

	def dispatch_ussd_request(self, http_request):
		request = self.make_ussd_request(http_request)
		app_code, app = self.match_ussd_app(request)
		request.intup_string = request.ussd_string[len(app_code):]

		response = self.process_ussd_request(app, request)
		if response is None:
			response = app(request)
		return self.process_ussd_response(app, response) or response








# CON, END, screen









