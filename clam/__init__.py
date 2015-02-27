import re
import os
import sys
import itertools
import urlparse
from config import config
from util import ClamFieldStorage

import logging
logging.basicConfig(format='%(process)-6d %(levelname)-8s %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

def filter_by_list(fdict, flist):
	def inner(key):
		return key[0] in flist
	return dict(filter(inner, fdict.items()))

class request(dict):
	def __init__(self, environ, re_args):
		self.args = re_args
		self.headers = [('content-type', 'text/html')]
		self.status = '200 OK'
		self.method = environ['REQUEST_METHOD']
		self._ENV = environ
		self._GET = self.__split_get()
		self._POST = self.__split_post()

	def set_status(self, status):
		self.status = status

	def __split_get(self):
		return urlparse.parse_qs(self._ENV.get('QUERY_STRING', ''), keep_blank_values=True)

	def __split_post(self):
		safe_env = filter_by_list(self._ENV, ['CONTENT_LENGTH', 'CONTENT_TYPE', 'REQUEST_METHOD'])
		return ClamFieldStorage(fp=self._ENV['wsgi.input'], environ=safe_env, keep_blank_values=1)

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
					req = request(environ, _fmt_grps(reg_search))
					func_output = reg_path[1](req)
			
					if func_output:
						func_output = ''.join(func_output)
					start_response(req.status, req.headers)
					return func_output or ''
				except Exception as e:
					import traceback
					logger.error("%s\t%s", e, traceback.format_exc())
					start_response('500 Internal Server Error', [('content-type', 'text/plain')], sys.exc_info())
					return "An incident has been recorded:\n" + repr(e)

		start_response('404 Not Found', [('content-type', 'text/html')])
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