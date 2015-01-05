#!/usr/bin/env python
import os
import sys
import time
import stat
import logging
from clam import clamengine, request, auth, fs
from clam.config import config
from templates import templates

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

application = clamengine()

@application.route('^/style.css$')
def rstyle(req):
	req.headers = [('content-type', 'text/css')]
	return templates.style()

@application.route('^/login$')
def page_login(req):
	if req.method == 'POST':
		un = req._POST.getvalue('username')
		pw = req._POST.getvalue('password')
		if not un or not pw:
			return templates.login()

		un = un.lower()
		if auth.auth_user(un, pw):
			auth.set_session(req, un)
			req.redirect = '/'
			return

	return templates.login()

@application.route('^/logout$')
def page_logout(req):
	if req.method == "POST":
		username = auth.get_session(req)
		if username:
			cs = req._POST.getvalue('cs')
			if cs:
				if cs == auth.hashcs(username):
					auth.set_session(req, '-', 'Thu, 01 Jan 1970 00:00:00 GMT')
	print username
	print cs
	req.redirect = '/'

@application.route('^/$')
def page_index(req):
	username = auth.get_session(req)
	if not username:
		req.redirect = '/login'
		return

	if 'oldpass' in req._POST and 'newpass' in req._POST:
		oldp = req._POST.getvalue('oldpass')
		newp = req._POST.getvalue('newpass')
		if auth.auth_user(username, oldp):
			auth.set_password(username, newp)
	
	dirname = ''
	if 'dir' in req._GET:
		dirname = req._GET['dir'][-1].strip('/\\')

	filename = ''
	if 'file' in req._GET:
		filename = req._GET['file'][-1].strip('/\\')


	# Determine pretty names for folders, used in HTML output
	p_dirname = fs.parentdir(dirname)
	s_dirname = fs.softdir(dirname)

	# Create absolute path of file or folder, used for security below
	path = fs.absjoin(
		config.file_root,
		username,
		dirname,
		filename,
	)

	# Protect us from writing to places we don't want
	try:
		fs.safepath(path)
	except AssertionError as e:
		return e.message

	# Handle folder creation
	if 'newfolder' in req._POST:
		nfolder = req._POST.getvalue('newfolder')
		if fs.app_create_folder(path, nfolder):
			req.redirect = '/?dir=' + dirname
			return

	# Handle file uploads
	if 'fileupload' in req._POST:
		files = req._POST['fileupload']
		if type(files) != list:
			files = [files]
		if files[-1].filename:
			if fs.app_file_uploads(path, files):
				req.redirect = '/?dir=' + dirname
				return

	if os.path.isfile(path):
		if 'delete' in req._GET:
			os.remove(path)
			req.redirect ='/?dir=' + dirname
			return

	if os.path.isdir(path):
		if 'delete' in req._GET:
			import shutil
			shutil.rmtree(path)
			req.redirect = '/?dir=' + p_dirname
			return
 
	if os.path.isdir(path):
		filelist = fs.listdir(path)
		content = []
		# If we are in the root don't add a "parent" option
		if not path == fs.absjoin(config.file_root, username):
			content.append(templates.parent(dirname=p_dirname, filename='..'))

		for f in filelist:
			if f[0]:
				content.append(templates.directory(dirname=os.path.join(dirname, f[1]), filename=f[1]))
			else:
				content.append(templates.file(dirname=dirname, filename=f[1]))

		return templates.index(
			title=os.sep if not dirname else dirname,
			username=username,
			content=templates.filelist(content='\n'.join(content)),
			cs=auth.hashcs(username),
			**fs.getspace()
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
	application.run(port=8000)