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

def safepath(directory, username='', exists=True):
	assert directory.startswith(config.file_root), "403, Access denied."
	assert directory.startswith(os.path.join(config.file_root, username)), "403, Access denied. User traversal."
	if not exists:
		return True
	assert os.path.exists(directory), "404, File does not exist."
	assert not os.path.islink(directory), "404, File does not exist."
	assert os.access(directory, os.R_OK), "403, You do not have permission to access this file."
	return True

def default_directory_create(username, parent, path):
	"""Create, using format /data/{username}/{parent}/{path} """
	if not path or path == '':
		return
	full_path = os.path.join(config.file_root, username, parent, path)
	try:
		safepath(full_path, username, exists=False)
	except AssertionError as ae:
		logger.warning(ae.message)
		return

	print os.mkdir(full_path)
	return True

def default_directory_delete(username, path):
	"""List directory contents, using format /data/{username}/{path} """
	try:
		safepath(path, username)
	except AssertionError as ae:
		logger.warning(ae.message)
		return

	import shutil
	shutil.rmtree(path)

def default_directory_list(username, path):
	"""List directory contents, using format /data/{username}/{path} """
	try:
		safepath(path, username)
	except AssertionError as ae:
		logger.warning(ae.message)
		return []

	f = os.listdir(path)
	return map(lambda x:(os.path.isdir(os.path.join(path, x)), x, humb(os.path.getsize(os.path.join(path, x)))), f)

def default_file_create(username, parent, file_object):
	"""Delete file, using format /data/{username}/{path} """
	print 'stack'
	if not file_object.file:
		return False
	fn = file_object.filename
	if not fn or fn.startswith('.'): #dont allow uploading dot files
		return
	# filecontent = file_object.file.read()
	full_path = os.path.join(config.file_root, username, parent, fn)

	if safepath(full_path, username, exists=False):
		with open(full_path, 'wb') as ouf:
			ts = datetime.datetime.now()
			logger.debug('Writing file to disk at location "%s"', full_path)
			# import IPython
			# IPython.embed()

			while True:
				x = file_object.file.read(1024)
				if not x:
					break
				ouf.write(x)
			# ouf.write(filecontent)
			logger.info('File write complete for location "%s", in duration "%s"', full_path, (datetime.datetime.now() - ts).total_seconds())
	return True

def default_file_delete(req, username, path):
	"""Delete file, using format /data/{username}/{path} """
	try:
		safepath(path, username)
	except AssertionError as ae:
		logger.warning(ae.message)
		return
	return os.remove(path)

def default_file_read(req, username, path, filename):
	"""Delete file, using format /data/{username}/{path} 
	If the file exists append the request headers and return the file"""
	try:
		safepath(path, username)
	except AssertionError as ae:
		logger.warning(ae.message)
		return

	mimetype, encoding = mimetypes.guess_type(path)
	if encoding:
		req.headers.append(('Content-Encoding', encoding))
	if mimetype:
		req.headers.append(('Content-Type', mimetype))
	req.headers.append(('Content-Disposition', 'filename="%s"' % filename))
	return open(path, 'rb').read()


hook.register('directory_create', default_directory_create)
hook.register('directory_delete', default_directory_delete)
hook.register('directory_list', default_directory_list)
hook.register('file_create', default_file_create)
hook.register('file_delete', default_file_delete)
hook.register('file_read', default_file_read)