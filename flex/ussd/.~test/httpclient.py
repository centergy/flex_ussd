from .auth import get_superuser, get_auth_client, get_request_token, get_access_token, parse_superuser
from client.tokens.models import Request as RequestTokenModel, Access as AccessTokenModel
from .utils import validate_response_json, validate_response_status_code
from passport.models import Passport as PassportModel
from .passports import get_passport, parse_passport
from django.test.client import Client as BaseClient
from client.models import Client as AuthClientModel
from django.contrib.auth import get_user_model
from django.utils.functional import curry
from collections import defaultdict
from requests import Session
import sys

if sys.version_info < (3,0):
	from urlparse import urlparse
else:
	from urllib.parse import urlparse



class HttpClient(Session):
	"""A class that can act as a client for testing purposes."""
	ACCESS_TOKEN = 'access'
	REQUEST_TOKEN = 'request'
	CLIENT_TOKEN = 'client'

	auth_token_names = frozenset(('access', 'request', 'client'))

	environ_dirt = frozenset(('superuser', 'token', 'me', 'auth'))

	def __init__(self, server=None,  **defaults):
		super(HttpClient, self).__init__()
		self.server = server
		self.defaults = defaults
		self.token_cache = defaultdict(dict)

	@property
	def url(self):
		return self.server.url if self.server else None

	def request(self, method, url='', **kwargs):
		request = self._base_environ(method=method, url=url, **kwargs)

		method = request.pop('method')
		url = request.pop('url')
		response = super(HttpClient, self).request(method, url, **request)
		# if response:
		# 	response.validate = curry(self._validate_response, response)
		return response

	def _validate_response(self, response, status_code=200, redirect=False, **extra):
		if status_code:
			validate_response_status_code(response.status_code, status_code, redirect)

		if 'application/json' in response.get('Content-Type'):
			validate_response_json(response.json(), **extra)

	def _base_environ(self, **request):
		environ = {
			'headers' : {}
		}
		environ.update(self.defaults)
		environ['headers'].update(request.pop('headers', {}))
		environ.update(request)

		environ['headers']['Authorization'] = self._get_auth_header(environ)
		environ['url'] = self._get_request_url(environ)
		return self._clean_environ(environ)

	def _clean_environ(self, environ):
		for k in self.environ_dirt:
			environ.pop(k, None)
		return environ

	def _get_request_url(self, environ):
		url = environ.get('url', '')
		parts = urlparse(url)
		if not parts.netloc:
			if not self.url:
				raise ValueError('Http request sessions created with no test'\
					' server require full urls.')
			return self.url.rstrip('/') + '/' + url.lstrip('/')
		return url

	def _get_auth_header(self, environ):
		"""get the Authorization header for the request."""
		header = environ.get('auth')
		if header is None or header in self.auth_token_names:
			token = header or environ.get('token', self.ACCESS_TOKEN)
			if token == self.CLIENT_TOKEN:
				header = self._get_auth_client(environ).auth_header()
			elif token == self.REQUEST_TOKEN:
				header = self._get_request_token(environ).auth_header()
			elif token == self.ACCESS_TOKEN:
				header = self._get_access_token(environ).auth_header()
			else:
				raise ValueError('Invalid auth token type: {}. '\
					'Allowed values: Client.ACCESS_TOKEN, Client.REQUEST_TOKEN '\
					'or Client.CLIENT_TOKEN.'.format(token))
		return str(header)

	def _get_superuser(self, environ):
		user = parse_superuser(environ.get('superuser'), {})
		if user and isinstance(user, get_user_model()):
			return user
		return get_superuser(**user)

	def _get_auth_client(self, environ):
		user = self._get_superuser(environ)
		client = self.token_cache[self.CLIENT_TOKEN].get(user)
		if client:
			return client
		rv = self.token_cache[self.CLIENT_TOKEN][user] = get_auth_client(user)
		return rv

	def _get_request_token(self, environ):
		client = self._get_auth_client(environ)
		request = self.token_cache[self.REQUEST_TOKEN].get(client)
		if request:
			return request
		rv = self.token_cache[self.REQUEST_TOKEN][client] = get_request_token(client)
		return rv

	def _get_access_token(self, environ):
		me = self._get_passport(environ)
		access = self.token_cache[self.ACCESS_TOKEN].get(me.who)
		if access:
			return access
		request = self._get_request_token(environ)
		rv = get_access_token(passport=me, request=request)
		self.token_cache[self.ACCESS_TOKEN][me.who] = rv
		return rv

	def _get_passport(self, environ):
		me = parse_passport(environ.get('me'), {})
		if me and isinstance(me, PassportModel):
			return me
		return get_passport(**me)
