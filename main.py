#!/usr/bin/env python
import hashlib
import itertools
import json
import os
import sys
import time
from clam import clamengine, request, util, hook, config, logger
from plugins import *
from templates import templates

application = clamengine()

@application.route('^/debug$')
def rdebug(req):
	req.set_status("301 Redirect")
	req.headers = [('Location', '/')]
	return ''

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
		auth = hook.authentication(un)
		if any(auth.password_verify(pw)):
			s = hook.session(req)
			if any(s.set(un)):
				req.redirect = '/'
				return

	return templates.login()

@application.route('^/logout$')
def page_logout(req):
	if req.method == "POST":
		if csrfcheck(req):
			s = hook.session(req)
			list(s.expire())

	req.set_status("301 Redirect")
	req.headers = [('Location', '/')]

@application.route('^/$')
def page_index(req):
	s = hook.session(req)
	username = list(s.get())[-1]
	if not username:
		req.set_status("301 Redirect")
		req.headers = [('Location', '/login')]
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
			req.set_status("301 Redirect")
			req.headers = [('Location', '/?dir=' + dirname)]
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
		return

	# Handle filesystem actions like delete
	for action in [x for x in req._GET.keys() if x not in ['dir', 'file']]:
		racton = filter(None, fs.action(action, filename))
		if racton:
			req.set_status("301 Redirect")
			req.headers = [('Location', '/?dir=' + racton[0])]
			return

	# Handle directory list or delete
	if not filename:
		filelist = fs.directory_read()
		content = []

		for f in filelist:
			# Horrible hacky actions templating
			shadow_actions = []
			for ac in f['actions']:
				shadow_actions.append(templates.actions(path=f['path'], name=f['name'], file=f['file'], action=ac))
			f['actions'] = shadow_actions

			if f['isdir']:
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
		f = list(fs.file_read(filename))
		if len(f) > 1:
			logger.critical('File read response from multiple hooks')

		req.headers = [('content-disposition', 'filename="%s"' % filename)]
		import mimetypes
		mtype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
		if mtype:
			req.headers.append(('content-type', mtype))
		return f[0]

		
if __name__ == '__main__':
	application.run(port=8080)