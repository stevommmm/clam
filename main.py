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
	s = hook.session(req)
	username = s.get()[-1]
	if username:
		cs = req._POST.getvalue('cs')
		if cs:
			if cs == hashlib.sha1(username + config.secret).hexdigest():
				return True
	return false

@application.route('^/style.css$')
def rstyle(start_response, req):
	start_response('200 OK', [('content-type', 'text/css')])
	return templates.style()

@application.route('^/login$')
def page_login(start_response, req):
	if req.method == 'POST':
		un = req._POST.getvalue('username')
		pw = req._POST.getvalue('password')
		if not un or not pw:
			return templates.login()

		un = un.lower()
		auth = hook.authentication(un)
		if any(auth.password_verify(pw)):
			s = hook.session(req)
			if any(s.set(un)):
				req.redirect = '/'
				return

	start_response('200 OK', req.headers)
	return templates.login()

@application.route('^/logout$')
def page_logout(start_response, req):
	if req.method == "POST":
		if csrfcheck(req):
			s = hook.session(req)
			list(s.expire())
	start_response('301 Redirect', [('Location', '/')])

@application.route('^/$')
def page_index(start_response, req):
	s = hook.session(req)
	username = list(s.get())[-1]
	if not username:
		req.redirect = '/login'
		return

	if 'oldpass' in req._POST and 'newpass' in req._POST and csrfcheck(req):
		oldp = req._POST.getvalue('oldpass')
		newp = req._POST.getvalue('newpass')
		auth = hook.authentication(username)
		if any(auth.password_verify(pw)):
			list(auth.password_set(newp))
	
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
			start_response('301 Redirect', [('Location', '/?dir=' + dirname)])
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
			start_response('200 OK', req.headers)
			return 'OK'

	# Handle directory list or delete
	if not filename:
		if 'delete' in req._GET and dirname != '':
			if any(fs.directory_delete(dirname)):
				start_response('301 Redirect', [('Location', '/?dir=' + dirname)])
			else:
				start_response('500 Internal Server Error', req.headers)
			return

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

		start_response('200 OK', req.headers)
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
				start_response('301 Redirect', [('Location', '/?dir=' + dirname)])
			else:
				start_response('500 Internal Server Error', req.headers)
			return
		else:
			f = list(fs.file_read(filename))
			if len(f) > 1:
				logger.critical('File read response from multiple hooks')

			req.headers = [('content-disposition', 'filename="%s"' % filename)]
			import mimetypes
			mtype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
			if mtype:
				req.headers.append(('content-type', mtype))
			start_response('200 OK', req.headers)
			return f[0]

		
if __name__ == '__main__':
	application.run(port=8080)