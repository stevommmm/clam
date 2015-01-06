#!/usr/bin/env python
import os
import sys
import hashlib
import time
import itertools
from clam import clamengine, request, util, hook, config, logger
from templates import templates
from plugins import *

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
		if any(hook.call('auth_user', req, un, pw)):
			hook.call('set_session', req, un)
			req.redirect = '/'
			return

	return templates.login()

@application.route('^/logout$')
def page_logout(req):
	if req.method == "POST":
		username = hook.call('get_user', req)[-1]
		if username:
			cs = req._POST.getvalue('cs')
			if cs:
				if cs == hashlib.sha1(username + config.secret).hexdigest():
					hook.call('set_session', req, '-', 'Thu, 01 Jan 1970 00:00:00 GMT')
	req.redirect = '/'

@application.route('^/$')
def page_index(req):
	username = hook.call('get_user', req)[-1]
	if not username:
		req.redirect = '/login'
		return

	if 'oldpass' in req._POST and 'newpass' in req._POST:
		oldp = req._POST.getvalue('oldpass')
		newp = req._POST.getvalue('newpass')
		if any(hook.call('auth_user', req, username, oldp)):
			hook.call('set_user_password', username, newp)
	
	dirname = ''
	if 'dir' in req._GET:
		dirname = req._GET['dir'][-1].strip('/\\')

	filename = ''
	if 'file' in req._GET:
		filename = req._GET['file'][-1].strip('/\\')

	# Determine pretty names for folders, used in HTML output
	p_dirname = util.parentdir(dirname)
	s_dirname = util.softdir(dirname)

	# Create absolute path of file or folder, used for security below
	path = util.absjoin(
		config.file_root,
		username,
		dirname,
		filename,
	)

	# Protect us from writing to places we don't want
	try:
		util.safepath(path)
	except AssertionError as e:
		return e.message

	# Handle folder creation
	if 'newfolder' in req._POST:
		nfolder = req._POST.getvalue('newfolder')
		if any(hook.call('directory_create', username, path, nfolder)):
			req.redirect = '/?dir=' + dirname
			return

	# Handle file uploads
	if 'fileupload' in req._POST:
		files = req._POST['fileupload']
		if type(files) != list:
			files = [files]
		if files[-1].filename:
			for f in files:
				list(hook.call('file_create', username, path, f))

			req.redirect = '/?dir=' + dirname
			return

	# Handle directory list or delete
	if os.path.isdir(path):
		if 'delete' in req._GET:
			hook.call('directory_delete', username, path)
			req.redirect = '/?dir=' + p_dirname
			return

		filelist = itertools.chain.from_iterable(hook.call('directory_list', username, path))
		content = []
		# If we are in the root don't add a "parent" option
		if not path == util.absjoin(config.file_root, username):
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
			cs=hashlib.sha1(username + config.secret).hexdigest(),
			**util.getspace()
		)

	# Handle file read or delete
	if os.path.isfile(path):
		if 'delete' in req._GET:
			hook.call('file_delete', req, username, path)
			req.redirect ='/?dir=' + dirname
		else:
			f = list(hook.call('file_read', req, username, path, filename))
			if len(f) > 1:
				logger.critical('File read response from multiple hooks')
			return f[0]

		
if __name__ == '__main__':
	application.run(port=8000)