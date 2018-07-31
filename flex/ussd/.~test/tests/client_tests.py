from passport.models import create_who_string
from ..passports import get_passport
from ..testclient import Client
from .. import exc
import pytest


xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize

pytestmark = pytest.mark.usefixtures("db")


@pytest.mark.testingtool
@pytest.mark.incomplete('Test the _get_* token methods and make sure they are catching.')
class ClientTest(object):
	"""docstring for ClientTestCase incomplete"""

	def test_auth_client(self):
		client = Client()
		response = client.post('/v2/auth/request/create', token='client')
		data = response.json()
		assert data['code'] == 200

	def test_the_client_fixture(self, client):
		response = client.post('/v2/auth/request/create', token='client')
		data = response.json()
		assert data['code'] == 200

	def test_request_token(self):
		client = Client()
		data= dict(username = 'whoami_whoami')
		response = client.post('/v2/passport/check', data=data, token='request')
		assert response.json().get('code') == 200

	def test_access_token(self, me):
		client = Client()
		response = client.post('/v2/passport/me')
		data = response.json()
		assert data['code'] == 200
		id = data.get('response', {}).get('results', {}).get('ID')
		assert id == me.who

	def test_with_passport_instance_as_me(self, client):
		passport = get_passport('whoami', '+25471111111111')
		response = client.post('/v2/passport/me', me=passport)
		data = response.json()
		assert data['code'] == 200
		id = data.get('response', {}).get('results', {}).get('ID')
		assert id == passport.who

	def test_with_who_as_me(self, client):
		passport = get_passport('whoami', '+25471111111111')
		response = client.post('/v2/passport/me', me=passport.who)
		data = response.json()
		assert data['code'] == 200
		id = data.get('response', {}).get('results', {}).get('ID')
		assert id == passport.who

	def test_with_username_as_me(self, client):
		passport = get_passport('whoami', '+25471111111111')
		response = client.post('/v2/passport/me', me=passport.username)
		data = response.json()
		assert data['code'] == 200
		id = data.get('response', {}).get('results', {}).get('ID')
		assert id == passport.who

	def test_with_phone_number_as_me(self, client):
		passport = get_passport('whoami', '+25471111111111')
		response = client.post('/v2/passport/me', me=passport.phone_number)
		data = response.json()
		assert data['code'] == 200
		id = data.get('response', {}).get('results', {}).get('ID')
		assert id == passport.who

	def test_with_new_passport_dict_as_me(self, client):
		passport = dict(username='whoami', phone_number='+25471111111111')
		response = client.post('/v2/passport/me', me=passport)
		data = response.json()
		assert data['code'] == 200
		results = data.get('response', {}).get('results', {})
		assert passport['username'] == results.get('username')
		assert passport['phone_number'] == results.get('phoneNumber')

	@xfail(raises=exc.TestPassportError, strict=True)
	def test_with_invalid_who_as_me(self, client):
		response = client.post('/v2/passport/me', me=create_who_string('whoami_whoami'))

	@xfail(raises=exc.TestPassportError, strict=True)
	def test_with_invalid_username_as_me(self, client):
		response = client.post('/v2/passport/me', me='whoami')

	@xfail(raises=exc.TestPassportError, strict=True)
	def test_with_invalid_phone_number_as_me(self, client):
		response = client.post('/v2/passport/me', me='+25471111111111')