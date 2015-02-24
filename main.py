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

def csrfcheck(req):
	username = hook.call('get_session', req)[-1]
	if username:
		cs = req._POST.getvalue('cs')
		if cs:
			if cs == hashlib.sha1(username + config.secret).hexdigest():
				return True
	return false


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
		if any(hook.call('verify_user_password', req, un, pw)):
			hook.call('set_session', req, un)
			req.redirect = '/'
			return

	return templates.login()

@application.route('^/logout$')
def page_logout(req):
	if req.method == "POST":
		if csrfcheck(req):
			hook.call('set_session', req, '-', 'Thu, 01 Jan 1970 00:00:00 GMT')
	req.redirect = '/'

@application.route('^/$')
def page_index(req):
	username = hook.call('get_session', req)[-1]
	if not username:
		req.redirect = '/login'
		return

	if 'oldpass' in req._POST and 'newpass' in req._POST and csrfcheck(req):
		oldp = req._POST.getvalue('oldpass')
		newp = req._POST.getvalue('newpass')
		if any(hook.call('verify_user_password', req, username, oldp)):
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


	# Protect us from writing to places we don't want
	try:
		fs = hook.filesystem(username, dirname)
	except AssertionError as e:
		return e.message

	# Handle folder creation
	if 'newfolder' in req._POST and csrfcheck(req):
		nfolder = req._POST.getvalue('newfolder')
		if any(fs.directory_write(nfolder)):
			req.redirect = '/?dir=' + dirname
			return

	# Handle file uploads
	if 'fileupload' in req._POST:
		files = req._POST['fileupload']
		if type(files) != list:
			files = [files]
		if files[-1].filename:
			for f in files:
				if not f.file:
					break
				fn = f.filename
				if not fn or fn.startswith('.'): #dont allow uploading dot files
					break
				if any(fs.file_write(fn, f.file)):
					logger.info("Wrote %s to storage", fn)

			return 'OK'

	# Handle directory list or delete
	if not filename:
		if 'delete' in req._GET and dirname != '':
			if any(fs.directory_delete(dirname)):
				req.redirect = '/?dir=' + p_dirname
				return 'OK'
			return 'Error'

		filelist = fs.directory_read()
		content = []

		for f in filelist:
			if f['isdir']:
				if f['name'] == '..':
					content.append(templates.parent(**f))
				else:
					content.append(templates.directory(**f))
			else:
				content.append(templates.file(**f))

		return templates.index(
			title=os.sep if not dirname else dirname,
			username=username,
			content=templates.filelist(content='\n'.join(content)),
			cs=hashlib.sha1(username + config.secret).hexdigest(),
			**fs.getusage()
		)

	# Handle file read or delete
	if filename:
		if 'delete' in req._GET and filename != '':
			if any(fs.file_delete(filename)):
				req.redirect ='/?dir=' + dirname
				return 'OK'
			return 'Error'
		else:
			f = list(hook.call('file_read', req, username, path, filename))
			if len(f) > 1:
				logger.critical('File read response from multiple hooks')
			return f[0]

		
if __name__ == '__main__':
	application.run(port=8080)