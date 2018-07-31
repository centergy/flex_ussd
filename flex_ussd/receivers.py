from urllib.parse import parse_qs
from django.core import signals as djsignals
from django.dispatch import receiver


@receiver(djsignals.request_started, dispatch_uid='ussd._push_request_context')
def _push_request_context(sender, environ=None, **kwargs):
	from pprint import pprint

	print('')
	print('_'*200)
	print('Initial Environ')
	print('-'*200)
	pprint(environ, indent=4, depth=8)
	print('-'*200, '\n')


	build_environ(environ)

	print('-'*200)
	print('New Environ')
	print('-'*200)
	pprint(environ, indent=4, depth=8)
	print('-'*200)
	print('_'*200)



def build_environ(environ):
	if environ.get('PATH_INFO', '').startswith('/ussd/'):
		qs = parse_qs(environ.get('QUERY_STRING', ''))
		ussdpath = qs.get('menu_string')
		if ussdpath:
			ussdpath = _process_menu_string(ussdpath[0])
		else:
			ussdpath = ""
		environ['PATH_INFO'] = '/u/%s' % ussdpath
	return environ



def _process_menu_string(menu_string):
	back_menu= _back_menu_key_process(_main_menu_key_process(menu_string)) #process and return
	return _process_98(back_menu)



def _main_menu_key_process(string): #process *00
	back_btn_pos=string.rfind('*99')#get position of our 00 for back
	if (-1==back_btn_pos):
		return string
	elif string.endswith('*99'):#just go back to main
		return string[:0]
	else:
		return string[:0]+string[(back_btn_pos)+4:]


def _process_98(string):
	#make this a loop
	while (string.find('*98') is not -1):
		string=string.replace('*98','')
	return string


def _back_menu_key_process(string): #process any *0
	while (string.find('*0') is not -1):
		zero_pos=string.find('*0')
		if zero_pos is not -1:
			f_part=string[:zero_pos-2]
			l_part=string[zero_pos+2:]
			string=f_part+l_part
			string=string[:-1] if string.endswith('*') else string
		else:
			string=string[:-1] if string.endswith('*') else string
	return string




@receiver(djsignals.request_finished, dispatch_uid='ussd._pop_request_context')
def _pop_request_context(sender, **kwargs):
	pass
