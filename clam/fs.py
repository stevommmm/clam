import os
from clam.config import config

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

def listdir(directory):
	f = os.listdir(directory)
	if '.password' in f:
		f.remove('.password')
	return map(lambda x:(os.path.isdir(os.path.join(directory, x)), x), f)


def safepath(directory, exists=True):
	assert directory.startswith(config.file_root), "403, Access denied."
	if not exists:
		return True
	assert os.path.exists(directory), "404, File does not exist."
	assert not os.path.islink(directory), "404, File does not exist."
	assert os.access(directory, os.R_OK), "403, You do not have permission to access this file."
	return True

def app_create_folder(parent, directory):
	if not directory or directory == '':
		return False
	path = absjoin(parent, directory)
	if safepath(path, exists=False):
		return os.mkdir(path)

def app_file_uploads(parent, files):
	for f in files:
		if not f.file:
			return False
		fn = f.filename
		if fn.startswith('.'): #dont allow uploading dot files
			continue
		filecontent = f.file.read()
		fullfn = absjoin(parent, fn)
		if safepath(fullfn, exists=False):
			with open(fullfn, 'wb') as ouf:
				ouf.write(filecontent)
	return True

def getspace():
	s = os.statvfs(config.root)
	freegb = s.f_bavail * s.f_frsize / 1024 / 1024 / 1024
	totalgb = s.f_blocks * s.f_frsize / 1024 / 1024 / 1024
	return {'disk_percent': int(100 - (100 * float(freegb) / float(totalgb))), 'disk_ingb': freegb}