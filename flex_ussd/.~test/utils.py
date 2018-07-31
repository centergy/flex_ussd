import ipgetter


def validate_response_json(r, code=200, action=True, response=True, results=True):
	"""Validate an API response dict."""
	assert isinstance(r, dict)
	if code == True:
		assert 'code' in r
	elif code:
		assert r.get('code') == code

	if action == True:
		assert 'action' in r
	elif action:
		assert r.get('action') == action

	if response == True:
		assert 'response' in r
		assert isinstance(r['response'], dict)
	elif response:
		assert r.get('response') == response

	resp = r.get('response', {})
	if results == True:
		assert 'results' in resp
	elif results:
		assert resp.get('results') == results


_redirect_codes = frozenset((301, 302, 303, 307))

def validate_response_status_code(code, expected=200, redirect=False):
	if not isinstance(expected, (tuple, list, set, frozenset)):
		expected = (expected,)
	expected = set(expected)
	if redirect:
		expected.update(_redirect_codes)
	assert code in expected



_last_public_ip = None

def get_my_public_ip():
	global _last_public_ip
	if not _last_public_ip:
		_last_public_ip = ipgetter.myip() or '0.0.0.0'
	return _last_public_ip