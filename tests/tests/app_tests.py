import pytest
from flex.ussd.core import UssdApp

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize

# pytestmark = pytest.mark.usefixtures("db")


class AppTest(object):

	def test_init(self):
		app = UssdApp('test_app')
		assert app.name == 'test_app'
