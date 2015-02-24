from clam import hook

class testfilesystem(hook.filesystem):

	def __init__(self, *args):
		pass

	def getcwd(self):
		pass

	def getusage(self):
		return (0, 0)

	def file_read(self, *args):
		pass

	def file_write(self, *args):
		pass

	def file_delete(self, *args):
		pass

	def directory_write(self, *args):
		pass

	def directory_delete(self, *args):
		pass

	def directory_read(self):
		return [{
			'isdir': False,
			'name': 'MEOW.dat',
			'size': '100 GB',
			'path': '',
		}]