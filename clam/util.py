import cgi
import os
from clam import config


class ClamFieldStorage(cgi.FieldStorage):
	def make_file(self, binary=None):
		import tempfile
    	return tempfile.TemporaryFile("w+b", dir=config.tmp_root)

	def __repr__(self):
		return "FieldStorage(%r, %r, ...)" % ( self.name, self.filename)


def path(username, directory=None, filepath=None):
	user_root = absjoin(config.file_root, username, 'files')
	assert user_root.startswith(config.file_root), "403, Access denied."

	dir_root = absjoin(user_root, directory)
	assert dir_root.startswith(user_root), "403, Access denied."

	file_root = absjoin(dir_root, filepath)
	assert dir_root.startswith(dir_root), "403, Access denied."

	return file_root

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

def safepath(directory, username='', exists=True):
	assert directory.startswith(config.file_root), "403, Access denied."
	assert directory.startswith(os.path.join(config.file_root, username)), "403, Access denied. User traversal."
	if not exists:
		return True
	assert os.path.exists(directory), "404, File does not exist."
	assert not os.path.islink(directory), "404, File does not exist."
	assert os.access(directory, os.R_OK), "403, You do not have permission to access this file."
	return True

def getspace():
	s = os.statvfs(config.root)
	freegb = s.f_bavail * s.f_frsize / 1024 / 1024 / 1024
	totalgb = s.f_blocks * s.f_frsize / 1024 / 1024 / 1024
	return {'disk_percent': int(100 - (100 * float(freegb) / float(totalgb))), 'disk_ingb': freegb}