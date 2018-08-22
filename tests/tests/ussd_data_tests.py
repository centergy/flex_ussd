import pytest
from flex.ussd.wrappers import UssdData

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize
skip = pytest.mark.skip

# pytestmark = pytest.mark.usefixtures("db")

class UssdDataChunkTest(object):

	@parametrize('raw,data', [
		('123*4*3*"my input"*00', ['123', '4', '3', 'my input', '00']),
		('123*my input*00*"wildcard*input"', ['123', 'my input', '00', 'wildcard*input']),
		(['123', '4', '3', 'my input', '00'], ['123', '4', '3', 'my input', '00']),
		(['123', 'my input', '00', 'wildcard*input'], ['123', 'my input', '00', 'wildcard*input']),
		pytest.param(['123', 4, '3', 'my input', '00'], ['123', '4', '3', 'my input', '00'], marks=xfail),
	])
	def test_init(self, raw, data):
		tv = UssdData(raw)
		assert len(tv.data) == len(data)
		assert tv.data == data
		assert tv.equals(data)

		tv2 = UssdData()
		tv2.data = data
		assert tv == tv2

	@parametrize('v1,v2,expected', [
		('123*4*3*"input"*00', '123*4*3*"input"*00', True),
		('123*4*3*"input"*00', '123*4*3*"input"', False),
		('123*4*3*"input"*00', '123*4*3*input*00', True),
		('123*4*3*"my input"*00', ['123', '4', '3', 'my input', '00'], True),
		('123*my input*00*"wildcard*input"', '123*my input*00*"wildcard*input"', True),
		('123*input*00*"wildcard*input"', '123*input*00*wildcard*input', False),
		('123*my input*00*"wildcard*input"', ['123', 'my input', '00', 'wildcard*input'], True),
		('123*my input*00*"wildcard*input"', ['123', 'my input', '00', 'wildcard', 'input'], False),
	])
	def test_equals(self, v1, v2, expected):
		subject = UssdData(v1)
		other = UssdData(v2)
		assert subject.equals(v1)
		assert subject.equals(v2) == expected
		assert subject.equals(other) == expected

	@parametrize('v1,v2,expected,start,end', [
		('123*4*3*"input"*00', '123*4*3*"input"*00', True, None, None),
		('123*4*3*"input"*00*', '123*4*3*"input"*00', True, None, None),
		('123*4*3*"input"*00', '123*4*3*"input"*00*', False, None, None),
		('123*4*3*"input"*00', '123*4*3*input', True, None, None),
		('123*4*3**"input"*00', '123*4*3**input', True, None, None),
		('123*4*3**"input"*00', '123*4*3*input', False, None, None),
		('123*4*3*"input"*00', '123*4*3*inp', False, None, None),
		('123*4*3*input*00', '123*4*3*input*34', False, None, None),
		('123*4*3*input*00', '3*input', True, 2, None),
		('123*4*3*input*00', '3*input', True, 2, -1),
		('123*4*3*input*00', '3*input', False, 2, -2),
		('123*00*"wildcard*input"*54', '123*00*"wildcard*input"', True, None, None),
		('123*00*"wildcard*input"', '123*00*"wildcard*"', False, None, None),
		('123*4*3*"my input"*00', ['123', '4', '3', 'my input'], True, None, None),
		('123*4*3*"my input"*00', ['123', '4', '3', 'my input', '0'], False, None, None),
		('123*input*00*"wildcard*input"', '123*input*00*wildcard*input', False, None, None),
		('123*00*"wildcard*input"*89', ['123', '00', 'wildcard*input'], True, None, None),
		('123*00*"wildcard*input"*89', ['123', '00', 'wildcard', 'input'], False, None, None),
	])
	def test_startswith(self, v1, v2, expected, start, end):
		subject = UssdData(v1)
		other = UssdData(v2)
		assert subject.startswith(v1)
		assert subject.startswith(v2, start, end) == expected
		assert subject.startswith(other, start, end) == expected

	@parametrize('v1,v2,expected,start,end', [
		('123*4*3*"input"*00', '123*4*3*"input"*00', True, None, None),
		('123*4*3*"input"*00*', '123*4*3*"input"*00', True, None, None),
		('123*4*3*"input"*00', '123*4*3*"input"*00*', False, None, None),
		('123*4*3*"input"*00', '123*4*3*input', True, None, None),
		('123*4*3**"input"*00', '123*4*3**input', True, None, None),
		('123*4*3**"input"*00', '123*4*3*input', False, None, None),
		('123*4*3*"input"*00', '123*4*3*inp', False, None, None),
		('123*4*3*input*00', '123*4*3*input*34', False, None, None),
		('123*4*3*input*00', '3*input', True, None, -2),
		('123*4*3*input*00', '3*input', True, 1, -2),
		('123*4*3*input*00', '3*input', False, 2, -2),
		('123*00*"wildcard*input"*54', '123*00*"wildcard*input"', True, None, None),
		('123*00*"wildcard*input"', '123*00*"wildcard*"', False, None, None),
		('123*input*00*"wildcard*input"', '123*input*00*wildcard*input', False, None, None),
	])
	def test_endswith(self, v1, v2, expected, start, end):
		v1, v2 = v1[-1::-1], v2[-1::-1]
		print(v1, v2)
		subject = UssdData(v1)
		other = UssdData(v2)
		assert subject.endswith(v1)
		assert subject.endswith(v2, start, end) == expected
		assert subject.endswith(other, start, end) == expected

	@skip
	def test_copy(self):
		assert False

	@parametrize('v1,v2,expected', [
		('123*4*3*"input"*00', '123*4*3*"input"*00', True),
		('123*4*3*"input"*00', '123*4*3*"input"', False),
		('123*4*3*"input"*00', '123*4*3*input*00', True),
		('123*4*3*"my input"*00', ['123', '4', '3', 'my input', '00'], True),
		('123*my input*00*"wildcard*input"', '123*my input*00*"wildcard*input"', True),
		('123*input*00*"wildcard*input"', '123*input*00*wildcard*input', False),
		('123*my input*00*"wildcard*input"', ['123', 'my input', '00', 'wildcard*input'], True),
		('123*my input*00*"wildcard*input"', ['123', 'my input', '00', 'wildcard', 'input'], False),
	])
	def test__eq__(self, v1, v2, expected):
		subject = UssdData(v1)
		other = UssdData(v2)
		assert (subject == other) == expected

	@skip
	def test__contains__(self):
		assert False

	@skip
	def test__le__(self):
		assert False

	@skip
	def test__ge__(self):
		assert False

