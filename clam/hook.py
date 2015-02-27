import collections
import os
import itertools
import hashlib
from Cookie import SimpleCookie
from clam import logger
from clam import config

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

	def action(self, action, request, filename):
		for c in self.children:
			if hasattr(c, 'action_%s' % action):
				yield getattr(c, 'action_%s' % action)(request, filename)

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
		return filter(None, [c.file_read(filename) for c in self.children])

	def file_write(self, filename, content):
		return [c.file_write(filename, content) for c in self.children]

	def directory_read(self):
		return itertools.chain.from_iterable([c.directory_read() for c in self.children])

	def directory_write(self, dirname):
		return [c.directory_write(dirname) for c in self.children]


class session(object):
	__metaclass__ = inheritors

	def __init__(self, request):
		self.children = []
		for c in session.__inheritors__[session]:
			self.children.append(c(request))

	def set(self, username, expires=None):
		return [c.set(username, expires) for c in self.children]

	def expire(self):
		return [c.expire() for c in self.children]

	def get(self):
		return [c.get() for c in self.children]

class authentication(object):
	__metaclass__ = inheritors

	def __init__(self, username):
		self.children = []
		for c in authentication.__inheritors__[authentication]:
			self.children.append(c(username))

	def password_verify(self, password):
		return [c.password_verify(password) for c in self.children]

	def password_set(self, password):
		return [c.password_set(password) for c in self.children]