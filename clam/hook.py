import collections
import os
import itertools
import hashlib
from Cookie import SimpleCookie
from clam import logger
from clam import config

hooks = collections.defaultdict(list)


def register(event_name, func):
	logger.info('Registered "%s" for event "%s:%s"', event_name, func.__name__, func.func_code.co_filename.split(os.sep)[-1])
	hooks[event_name].append(func)


def call(event_name, req, *args):
	retdata = []
	for x in hooks[event_name]:
		logger.debug('Dispatched "%s" to "%s:%s" with args %s', event_name, x.__name__, x.func_code.co_filename.split(os.sep)[-1], str(args))
		try:
			retdata.append(x(req, *args))
		except Exception as e:
			logger.critical(e)
	return retdata 


class inheritors(type):
	__inheritors__ = collections.defaultdict(list)

	def __new__(meta, name, bases, dct):
		klass = type.__new__(meta, name, bases, dct)
		for base in klass.mro()[1:-1]:
			logger.info('Registered %s.%s', klass.__module__, klass.__name__)
			meta.__inheritors__[base].append(klass)
		return klass


class filesystem(object):
	__metaclass__ = inheritors

	def __init__(self, username, directory):
		self.children = []
		for c in filesystem.__inheritors__[filesystem]:
			self.children.append(c(username, directory))

	def getcwd(self):
		mc = collections.Counter(itertools.chain.from_iterable([c.getcwd() for c in self.children]))
		try:
			return mc.most_common(1)[0][0]
		except IndexError:
			raise ValueError('No plugins returned a valid CWD')

	def getusage(self):
		us = [c.getusage() for c in self.children]
		freegb = sum([x[0] for x in us])
		totalgb = sum([x[1] for x in us])
		return {'disk_percent': int(100 - (100 * float(freegb) / float(totalgb))), 'disk_ingb': freegb}

	def file_read(self, filename):
		logger.info('file read %s', filename)
		return [c.file_read(filename) for c in self.children]

	def file_write(self, filename, content):
		logger.info('file write %s', filename)
		return [c.file_write(filename, content) for c in self.children]

	def file_delete(self, filename):
		logger.info('file del %s', filename)
		return [c.file_delete(filename) for c in self.children]

	def directory_read(self):
		return itertools.chain.from_iterable([c.directory_read() for c in self.children])

	def directory_write(self, dirname):
		return [c.directory_write(dirname) for c in self.children]

	def directory_delete(self, dirname):
		logger.info('dir del %s', dirname)
		return [c.directory_delete(dirname) for c in self.children]


class session(object):
	__metaclass__ = inheritors

	def __init__(self, request):
		self.children = []
		for c in session.__inheritors__[session]:
			self.children.append(c(request))

	def set(self, username, expires=None):
		logger.info('set sess %s', username)
		return [c.set(username, expires) for c in self.children]

	def expire(self):
		return [c.expire() for c in self.children]

	def get(self):
		logger.info('get sess')
		return [c.get() for c in self.children]