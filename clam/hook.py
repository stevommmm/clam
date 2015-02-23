import collections
import os
import itertools
from clam import logger

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
			meta.__inheritors__[base].append(klass)
		return klass

class filesystem(object):
	__metaclass__ = inheritors

	def __init__(self, username, directory):
		self.children = []
		for c in filesystem.__inheritors__[filesystem]:
			self.children.append(c(username, directory))

	def file_read(self, filename):
		return itertools.chain.from_iterable([c.file_read(filename) for c in self.children])

	def file_write(self, filename, content):
		return itertools.chain.from_iterable([c.file_write(filename, content) for c in self.children])

	def file_delete(self, filename):
		return itertools.chain.from_iterable([c.file_delete(filename) for c in self.children])

	def directory_read(self):
		return itertools.chain.from_iterable([c.directory_read() for c in self.children])

	def directory_write(self, dirname):
		return itertools.chain.from_iterable([c.directory_write(dirname) for c in self.children])

	def directory_delete(self):
		return itertools.chain.from_iterable([c.directory_delete() for c in self.children])


class session(object):
	__metaclass__ = inheritors