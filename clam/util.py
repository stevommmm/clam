import cgi
import os
from clam import config


class ClamFieldStorage(cgi.FieldStorage):
	def make_file(self, binary=None):
		import tempfile
		# return tempfile.TemporaryFile("w+b", dir=config.tmp_root)
		return tempfile.NamedTemporaryFile("w+b", dir=config.tmp_root)

	def __repr__(self):
		return "FieldStorage(%r, %r, ...)" % ( self.name, self.filename)

def absjoin(*args):
	return os.path.abspath(
		os.path.join(*args)
	)

def parentdir(directory):
	return os.sep.join(directory.split(os.sep)[:-1])

def softdir(directory):
	try:
		return directory.rstrip(os.sep).split(os.sep)[-1]
	except IndexError:
		return '/'