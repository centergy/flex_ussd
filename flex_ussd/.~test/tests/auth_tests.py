from ..auth import (
	AuthHeader, AuthClientModel, RequestTokenModel, AccessTokenModel,
	get_superuser, get_auth_client,	get_request_token, get_access_token,
)
from django.contrib.auth import get_user_model
from ..passports import get_passport
import procedures.validate
from .. import exc
import pytest
import six

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize

pytestmark = pytest.mark.usefixtures("db")


@pytest.mark.testingtool
class SuperuserTest(object):
	""":func:`..client.get_superuser` & fixture :func:`..fixtures.superuser`"""

	def test_default(self):
		admin = get_superuser()
		assert isinstance(admin, get_user_model())
		assert admin.pk
		assert admin == get_superuser()

	def test_the_fixture(self, superuser):
		assert isinstance(superuser, get_user_model())
		assert superuser.pk
		assert superuser == get_superuser()

	def test_with_different_settings(self, settings):
		default = get_superuser()
		attrs = dict(
				username = 'im_different',
				password = 'password',
				email = 'im_different@example.com'
			)
		settings.TEST_SUPER_USER = attrs
		diff = get_superuser()

		assert diff.username == attrs['username']
		assert diff.email == attrs['email']
		assert get_superuser() == diff
		assert default != diff

	def test_with_attributes_passed_as_kwargs(self, settings):
		attrs_1 = dict(
				username = 'im_different1',
				password = 'password',
				email = 'im_different1@example.com'
			)
		attrs_2 = dict(
				username = 'im_different2',
				password = 'password',
				email = 'im_different2@example.com'
			)
		admin_0 = get_superuser()

		settings.TEST_SUPER_USER = attrs_1
		admin_1 = get_superuser()
		admin_2 = get_superuser(**attrs_2)

		assert admin_2.username == attrs_2['username']
		assert admin_2.email == attrs_2['email']
		assert admin_0 != admin_2
		assert admin_1 != admin_2
		assert admin_0 != admin_1
		assert get_superuser() != admin_2



@pytest.mark.testingtool
class AuthClientTest(object):
	"""docstring for AuthClientTestCase"""

	def test_default(self, superuser):
		client = get_auth_client()
		assert isinstance(client, AuthClientModel)
		assert client.pk
		assert client == get_auth_client()
		assert client.user == superuser

	def test_the_fixture(self, auth_client, superuser):
		assert isinstance(auth_client, AuthClientModel)
		assert auth_client.pk
		assert auth_client == get_auth_client()
		assert auth_client.user == superuser

	@parametrize('user,is_default',[
		(None, True),
		('sudo', False),
		(dict(username='sudo'), False),
	])
	def test_with_different_user_arguments(self, user, is_default):
		client = get_auth_client(user)
		assert isinstance(client, AuthClientModel)
		assert client.pk
		assert client == get_auth_client(user)
		if is_default:
			assert client == get_auth_client()
		else:
			assert client != get_auth_client()

	def test_monkeypatched_auth_header(self):
		auth_client = get_auth_client()
		header = auth_client.auth_header()
		assert header
		assert isinstance(header, AuthHeader)
		assert 'clientKey' in header
		assert 'clientSecret' in header
		assert header['clientKey'] == auth_client.key
		assert header['clientSecret'] == auth_client.secret

	@pytest.mark.usefixtures("mock_get_oauth_header")
	def test_monkeypatched_auth_header_str(self):
		auth_client = get_auth_client()
		header = str(auth_client.auth_header())

		assert isinstance(header, six.string_types)
		assert header
		result = procedures.validate.get_authenticated_client(header)
		assert result == auth_client


@pytest.mark.testingtool
class RequestTokenTest(object):
	"""docstring for GetPassportTestCase"""

	def test_default(self, auth_client):
		request = get_request_token()
		other = get_request_token()
		assert isinstance(request, RequestTokenModel)
		assert request.pk
		assert request.client == auth_client
		assert request != other
		assert request.client == other.client

	def test_the_fixture(self, request_token):
		assert isinstance(request_token, RequestTokenModel)
		assert request_token.pk

	def test_with_other_client(self):
		default = get_request_token()
		client = get_auth_client('other')
		result = get_request_token(client=client)
		assert result.client == client
		assert result.client != default.client

	def test_with_other_user(self):
		default = get_request_token()
		user = get_superuser('other_user')
		result = get_request_token(user=user)
		assert result.client.user == user
		assert result.client.user != default.client.user

	def test_monkeypatched_auth_header(self):
		request = get_request_token()
		header = request.auth_header()
		assert header
		assert isinstance(header, AuthHeader)
		assert 'requestToken' in header
		assert 'requestSecret' in header
		assert header['requestToken'] == request.token
		assert header['requestSecret'] == request.secret

	@pytest.mark.usefixtures("mock_get_oauth_header")
	def test_monkeypatched_auth_header_str(self):
		request = get_request_token()
		header = str(request.auth_header())

		assert isinstance(header, six.string_types)
		assert header
		result = procedures.validate.get_authenticated_request(header)
		assert result == request



@pytest.mark.testingtool
class AccessTokenTest(object):
	"""docstring for GetPassportTestCase"""

	def test_default(self, me, auth_client):
		access = get_access_token()
		assert isinstance(access, AccessTokenModel)
		assert access.pk
		assert access.passport == me
		assert access.client == auth_client

	def test_the_fixture(self, access_token, me):
		assert isinstance(access_token, AccessTokenModel)
		assert access_token.pk
		assert access_token.passport == me

	def test_with_other_passport(self):
		default = get_access_token()
		passport = get_passport(username='foobar', phone_number='+25471111111111')
		result = get_access_token(passport=passport)
		assert result.passport == passport
		assert result.passport != default.passport

	def test_monkeypatched_auth_header(self):
		access = get_access_token()
		header = access.auth_header()
		assert header
		assert isinstance(header, AuthHeader)
		assert 'accessToken' in header
		assert 'accessSecret' in header
		assert header['accessToken'] == access.token
		assert header['accessSecret'] == access.secret

	@pytest.mark.usefixtures("mock_get_oauth_header")
	def test_monkeypatched_auth_header_str(self):
		access = get_access_token()
		header = str(access.auth_header())

		assert isinstance(header, six.string_types)
		assert header
		result = procedures.validate.get_authenticated_user(header)
		assert result == access.passport
