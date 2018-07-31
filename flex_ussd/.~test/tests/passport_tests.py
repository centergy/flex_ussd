from ..passports import PassportModel, get_passport
from .. import exc
import pytest
import six

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize

pytestmark = pytest.mark.usefixtures("db")

@pytest.mark.testingtool
class PassportTest(object):
	"""docstring for GetPassportTestCase"""

	def test_default(self):
		passport = get_passport()
		assert isinstance(passport, PassportModel)
		assert passport.pk
		assert passport == get_passport()

	def test_the_fixture(self, me):
		assert isinstance(me, PassportModel)
		assert me.pk
		assert me == get_passport()

	@parametrize('new_settings', [
		dict(username='im_different', phone_number='+25471111111111'),
		xfail(dict(who='whoami_whoami_whoami_whoami_whoami'))
	])
	def test_with_different_settings(self, new_settings, settings):
		default = get_passport()

		settings.TEST_PASSPORT = new_settings
		passport = get_passport()

		assert isinstance(passport, PassportModel)
		assert passport == get_passport()

		for k,v in new_settings.items():
			assert v == getattr(passport, k)

		assert passport != default

	def test_passing_who_as_param(self):
		passport = get_passport(username='paramed', phone_number='+25471111111111')
		who = passport.who
		result = get_passport(who=who)
		assert result == passport
		assert result.who == who
		assert result != get_passport()

	@xfail
	def test_passing_invalid_who_as_param(self):
		result = get_passport(who='whoami_whoami_whoami_whoami_whoami')
