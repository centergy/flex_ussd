import pytest
from memory_profiler import profile as mem_profile

xfail = pytest.mark.xfail
parametrize = pytest.mark.parametrize
# pytestmark = pytest.mark.usefixtures("db")

@pytest.mark.skip
class MiscTest(object):

	def test_list_slicing(self):
		from time import time
		big_list = list((x for x in range(999999, 999999+2500)))
		ns = 1000000
		# @mem_profile
		def fn(_slice=False):
			sls = []
			st = time()
			v = 0
			if _slice:
				for x in range(ns):
					sl = big_list[999:]
					v += len(sl)
			else:
				_sl = big_list[999:]
				for x in range(ns):
					sl = _sl
					v += len(sl)
			et = time()
			print(' -->  {:,} slices of size {:,} in {:,} secs'.format(ns, v, round(et-st, 4)))
			return sls
		fn()
		print()
		fn(True)
		assert False

	@parametrize('index', reversed([None, 0, -1, 999, -999]))
	def _test_list_getitem(self, index):
		self.fn(index)
		assert False

	def fn(self, i=None, silent=False):
		from time import time
		big_list = list((x for x in range(999999, 999999+9999)))
		ns = 1000000
		tt = 0
		st = time()
		if i is None:
			for x in range(ns):
				tt += 9999999
		else:
			for x in range(ns):
				tt += big_list[i]
		et = time()
		if not silent:
			print(' --> sums of {:,} items from index {} in {:,} secs'.format(ns, i, round(et-st, 5)), '=', tt)
			# print('')


