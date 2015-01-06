import re
import cgi
import itertools
import urlparse
import collections
from config import config

import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Overwrite the fieldstorage __repr__ method to not include the uploaded file binary, make logging much cleaner
cgi.FieldStorage.__repr__ = lambda x: "FieldStorage(%r, %r, \"...\")" % ( x.name, x.filename)

hooks = collections.defaultdict(list)

class hook(object):
	@staticmethod
	def register(event_name, func):
		logger.info('Registered "%s" for event "%s"', event_name, func.__name__)
		hooks[event_name].append(func)

	@staticmethod
	def call(event_name, req, *args):
		retdata = []
		for x in hooks[event_name]:
			logger.debug('Dispatched "%s" to "%s" with args %s', event_name, x.__name__, str(args))
			retdata.append(x(req, *args))
		return retdata 


def filter_by_list(fdict, flist):
	def inner(key):
		return key[0] in flist
	return dict(filter(inner, fdict.items()))

class request(dict):
	def __init__(self, func, environ, re_args):
		self.re_args = re_args
		self.headers = [('content-type', 'text/html')]
		self.method = environ['REQUEST_METHOD']
		self.redirect = None
		self._ENV = environ
		self._GET = self.__split_get()
		self._POST = self.__split_post()
		self.body = ''
		if type(re_args) == dict:
			fresult = func(self, **re_args)
		else:
			fresult = func(self, *re_args)
		if fresult:
			self.body += fresult

	def __split_get(self):
		return urlparse.parse_qs(self._ENV.get('QUERY_STRING', ''), keep_blank_values=True)

	def __split_post(self):
		safe_env = filter_by_list(self._ENV, ['CONTENT_LENGTH', 'CONTENT_TYPE', 'REQUEST_METHOD'])
		return cgi.FieldStorage(fp=self._ENV['wsgi.input'], environ=safe_env, keep_blank_values=1)

class clamengine(object):
	def __init__(self):
		self.routes = {}

	def route(self, path_pattern, function=None):
		'''Route decorator, @application_instance.route('^regex$')'''
		def wrapper(function):
			self.routes[re.compile(path_pattern)] = function
		return wrapper

	def wsgi(self, environ, start_response):
		'''WSGI compliant callable, only ever called from __call__'''
		def _fmt_grps(reg_search):
			f = reg_search.groupdict()
			if not f:
				f = reg_search.groups()
			return f
		
		path = environ['PATH_INFO']
	
		for reg_path in self.routes.items():
			reg_search = reg_path[0].match(path)
			if reg_search:
				try:
					req = request(reg_path[1], environ, _fmt_grps(reg_search))
					if req.redirect:
						req.headers.append(('Location', req.redirect))
						start_response('301 Redirect', req.headers)
						return ['']
					else:
						start_response('200 OK', req.headers)
						return str(req.body)
				except Exception as e:
					start_response('500 Internal Server Error', [('content-type', 'text/html')])
					return (repr(e),)

		start_response('404 NOT FOUND', [('content-type', 'text/html')])
		return ('Not Found',)

	def __call__(self, environ, start_response):
		return self.wsgi(environ, start_response)

	def run(self, host="0.0.0.0", port=8000):
		'''Run this instance of clamengine using simple_server'''
		from wsgiref.simple_server import make_server
		srv =  make_server(host, port, self)
		try:
			srv.serve_forever()
		except KeyboardInterrupt:
			print "Got CTRL + C. Sent shutdown to server."


if __name__ == '__main__':
	clamengine().run()