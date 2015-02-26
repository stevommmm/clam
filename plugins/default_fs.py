from clam import hook
from clam import config
from clam import logger
import os
import mimetypes
import datetime

def humb(size):
    """Human readable sizes, everything is in KB to begin with"""
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffixIndex = 0
    while size > 1024:
        suffixIndex += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f %s" % (1, size, suffixes[suffixIndex])

def total_seconds(td):
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

class defaultfilesystem(hook.filesystem):
	def __init__(self, username, directory=os.sep):
		self.username = username
		self.root = os.path.abspath(os.path.join(config.file_root, username, 'files')) + os.sep
		self.cwdname = directory
		self.cwd = os.path.join(self.root, directory.lstrip(os.sep))
		assert self.cwd.startswith(config.root)
		assert self.root.startswith(config.file_root), 'Invalid root: ' + self.root
		assert self.cwd.startswith(config.file_root), 'Invalid cwd: ' + self.cwd

	def getcwd(self):
		return self.cwd

	def getusage(self):
		s = os.statvfs(self.cwd)
		freegb = s.f_bavail * s.f_frsize / 1024 / 1024 / 1024
		totalgb = s.f_blocks * s.f_frsize / 1024 / 1024 / 1024
		return (freegb, totalgb)

	def file_read(self, filename):
		fullpath = os.path.join(self.cwd, filename)
		assert fullpath.startswith(self.cwd), 'Invalid file path'
		with open(fullpath, 'rb') as inf:
			while True:
				x = inf.read(4096)
				if not x:
					break
				yield x

	def file_write(self, filename, fh):
		fullpath = os.path.join(self.cwd, filename)
		assert fullpath.startswith(self.cwd), 'Invalid file path'
		with open(fullpath, 'wb') as onf:
			ts = datetime.datetime.now()
			while True:
				x = fh.read(4096)
				if not x:
					break
				onf.write(x)
			logger.info('File write complete for location "%s", in duration "%s"', filename, total_seconds(datetime.datetime.now() - ts))
			return onf.tell()

	def directory_read(self):
		if self.cwd != self.root:
			yield {
				'isdir': True,
				'name': '..',
				'file': '',
				'size': '',
				'path': os.sep.join(self.cwdname.rstrip(os.sep).split(os.sep)[:-1]),
				'actions': [],
			}

		for x in os.listdir(self.cwd):
			isdir = os.path.isdir(os.path.join(self.cwd, x))
			yield {
				'isdir': isdir, 
				'name': x,
				'file': '' if isdir else x,
				'size': humb(os.path.getsize(os.path.join(self.cwd, x))) if not isdir else '',
				'path': os.path.join(self.cwdname, x) if isdir else self.cwdname,
				'actions': ['delete'],
			}

	def directory_write(self, dirname):
		fullpath = os.path.join(self.cwd, dirname)
		assert fullpath.startswith(self.cwd), 'Invalid directory path'
		os.mkdir(fullpath)
		return os.path.isdir(fullpath)

	def action_delete(self, filename):
		fullpath = os.path.join(self.cwd, filename)
		assert fullpath.startswith(self.cwd), 'Invalid file path'
		logger.info('Removing %s', fullpath)
		if os.path.isdir(fullpath):
			import shutil
			shutil.rmtree(fullpath)
			return os.sep.join(self.cwdname.split(os.sep)[:-1]) or os.sep
		if os.path.isfile(fullpath):
			os.remove(fullpath)
			return self.cwdname
