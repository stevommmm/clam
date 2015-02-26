from clam import hook
from clam import config
from clam import logger
import os
import mimetypes
import datetime

def humb(size):
    """ Human readable sizes, everything is in KB to begin with """
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffixIndex = 0
    while size > 1024:
        suffixIndex += 1  # increment the index of the suffix
        size = size / 1024.0  # apply the division
    return "%.*f %s" % (1, size, suffixes[suffixIndex])

def total_seconds(td):
	""" python 2.6 compat, 2.7 includes this method in datetime """
	return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

class defaultfilesystem(hook.filesystem):
	"""	Default filesystem for Clam.

		Works off a directory structure of:
	 		$application / data / $username / files / $path

		On init we verify that we haven't traversed the tree 
		to somehow be below the root data/username directory.
		This check can throw AssertionError at runtime.

	"""
	def __init__(self, username, directory=os.sep):
		""" Creates a instance of filesystem rooted in the users directory """
		self.username = username
		self.root = self.__absjoin(config.file_root, username, 'files') + os.sep
		self.cwdname = directory
		self.cwd = self.__absjoin(self.root, directory.lstrip(os.sep))
		assert self.cwd.startswith(config.root)
		assert self.root.startswith(config.file_root), 'Invalid root: ' + self.root
		assert self.cwd.startswith(config.file_root), 'Invalid cwd: ' + self.cwd

	def __absjoin(self, *args):
		""" Absolute path joining, used for startswith(root) in later calls """
		return os.path.abspath(
			os.path.join(*args)
		)

	def getcwd(self):
		""" Counter.most_common will determine what this reports 
		    to the application as in the event of multiple filesystem plugins
		"""
		return self.cwd

	def getusage(self):
		""" Used to show capacity to the user, returns (free, total) in GB """
		s = os.statvfs(self.cwd)
		# Convert our block sizes into a meaningful file size
		freegb = s.f_bavail * s.f_frsize / 1024 / 1024 / 1024
		totalgb = s.f_blocks * s.f_frsize / 1024 / 1024 / 1024
		return (freegb, totalgb)

	def file_read(self, filename):
		""" Concat the filename with the cwd(), returns a generator yielding a byte string """
		fullpath = self.__absjoin(self.cwd, filename)
		assert fullpath.startswith(self.cwd), 'Invalid file path requested by %s' % self.username
		with open(fullpath, 'rb') as inf:
			while True:
				x = inf.read(4096)
				if not x:
					break
				yield x

	def file_write(self, filename, fh):
		""" Push data to the filesystem, written in chunks of 4k. fh is a file like object """
		fullpath = self.__absjoin(self.cwd, filename)
		assert fullpath.startswith(self.cwd), 'Invalid file path requested by %s' % self.username
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
		""" Our main list, output args are mostly passed straight to the templater
			If we are not at the root of our filesystem, return a 'parent' item for user navigation
		"""
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
		""" Directory creation through the side menu """
		fullpath = self.__absjoin(self.cwd, dirname)
		assert fullpath.startswith(self.cwd), 'Invalid directory path requested by %s' % self.username
		os.mkdir(fullpath)
		return os.path.isdir(fullpath)

	def action_delete(self, filename):
		""" Used for extra file actions such as delete, in this case filename can
			be empty in the event we are deleting a directory, in that event we return
			the parent directory to refresh to

			Any action_%s function could be called with an action attribute in the core
		"""
		fullpath = self.__absjoin(self.cwd, filename)
		assert fullpath.startswith(self.cwd), 'Invalid file path requested by %s' % self.username
		logger.info('Removing %s', fullpath)
		if os.path.isdir(fullpath):
			import shutil
			shutil.rmtree(fullpath)
			return os.sep.join(self.cwdname.split(os.sep)[:-1]) or os.sep
		if os.path.isfile(fullpath):
			os.remove(fullpath)
			return self.cwdname
