#!/usr/bin/env python
import os
import sys
import time
import stat
from lucid import lucid, request
from templates import templates

class config:
	root = os.path.abspath(os.path.dirname(__file__))
	file_root = os.path.join(root, 'files')

application = lucid()

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
	return map(lambda x:(os.path.isdir(os.path.join(directory, x)), x), f)


@application.route('^/style.css$')
def rstyle(req):
	req.headers = [('content-type', 'text/css')]
	return templates.style()

@application.route('^/$')
def page_index(req):
	dirname = ''
	if 'dir' in req._GET:
		dirname = req._GET['dir'][-1].strip('/\\')

	filename = ''
	if 'file' in req._GET:
		filename = req._GET['file'][-1].strip('/\\')

	# Handle file uploads
	if 'fileupload' in req._POST:
		files = req._POST['fileupload']
		if type(files) != list:
			files = [files]

		for f in files:
			fn = f.filename
			filecontent = f.file.read()
			fullfn = absjoin(config.file_root, dirname, fn)
			print fullfn
			with open(fullfn, 'wb') as ouf:
				ouf.write(filecontent)


	# Determine pretty names for folders, used in HTML output
	p_dirname = parentdir(dirname)
	s_dirname = softdir(dirname)

	# Create absolute path of file or folder, used for security below
	path = absjoin(
		config.file_root, 
		dirname,
		filename,
	)

	# Protect us from writing to places we don't want
	if not path.startswith(config.root):
		return "403, Access denied."
	if not os.path.exists(path) or os.path.islink(path):
		return "404, File does not exist."
	if not os.access(path, os.R_OK):
		return "403, You do not have permission to access this file."

	if os.path.isfile(path):
		if 'delete' in req._GET:
			os.remove(path)
			path = os.path.dirname(path)


	if os.path.isdir(path):
		filelist = listdir(path)
		content = []
		# If we are in the root don't add a "parent" option
		if not path == config.file_root:
			content.append(templates.directory(dirname=p_dirname, filename='..'))

		for f in filelist:
			if f[0]:
				content.append(templates.directory(dirname=os.path.join(dirname, f[1]), filename=f[1]))
			else:
				content.append(templates.file(dirname=dirname, filename=f[1]))

		return templates.index(
			title=os.sep if not dirname else dirname,
			content=templates.filelist(content='\n'.join(content))
		)

	if os.path.isfile(path):
		import mimetypes
		mimetype, encoding = mimetypes.guess_type(path)

		if encoding:
			req.headers.append(('Content-Encoding', encoding))
		if mimetype:
			req.headers.append(('Content-Type', mimetype))
		req.headers.append(('Content-Disposition', 'filename="%s"' % filename))

		return open(path, 'rb').read()

	




if __name__ == '__main__':
	application.run(port=9000)