#!/usr/bin/env python
import os
import sys
import time
import stat
import logging
import hashlib
from Cookie import SimpleCookie
from clamengine import clamengine, request
from templates import templates

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

class config:
	root = os.path.abspath(os.path.dirname(__file__))
	file_root = os.path.join(root, 'files')
	secret = 'supersecretstring'

if not os.path.exists(config.file_root):
	os.mkdir(config.file_root)

application = clamengine()

def set_session(req, username, expires=None):
	s = username + ":" + req._ENV.get('REMOTE_ADDR', '-')
	s_hash = hashlib.sha1(s + config.secret).hexdigest()

	session_cookie = SimpleCookie()
	session_cookie['clamsession'] = s + ":" + s_hash
	session_cookie['clamsession']["path"] = '/'
	session_cookie['clamsession']["httponly"] = True
	if expires:
		session_cookie['clamsession']["expires"] = expires
	req.headers += [("set-cookie", m.OutputString()) for m in session_cookie.values()]

def get_session(req):
	s = req._ENV.get('HTTP_COOKIE', None)
	if not s:
		return None
	session_cookie = SimpleCookie(s)

	if not 'clamsession' in session_cookie:
		return None

	username, remote, uhash = session_cookie['clamsession'].value.split(':')
	s_hash = hashlib.sha1(username + ":" + remote + config.secret).hexdigest()
	if uhash == s_hash:
		if remote == req._ENV.get('REMOTE_ADDR', '-'):
			return username

def auth_user(username, password):
	pwh = hashlib.sha1(password + config.secret).hexdigest()
	pwf = os.path.join(config.file_root, username, '.password')
	if safepath(pwf):
		return pwh.strip() == open(pwf, 'rb').read().strip()
	return False

def set_password(username, password):
	pwh = hashlib.sha1(password + config.secret).hexdigest()
	pwf = os.path.join(config.file_root, username, '.password')
	if safepath(pwf):
		with open(pwf, 'wb') as f:
			f.write(pwh)


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
		if auth_user(un, pw):
			set_session(req, un)
			req.redirect = '/'
			return

	return templates.login()

@application.route('^/logout$')
def page_logout(req):
	set_session(req, '-', 'Thu, 01 Jan 1970 00:00:00 GMT')
	req.redirect = '/'

@application.route('^/$')
def page_index(req):
	username = get_session(req)
	if not username:
		req.redirect = '/login'
		return

	if 'oldpass' in req._POST and 'newpass' in req._POST:
		oldp = req._POST.getvalue('oldpass')
		newp = req._POST.getvalue('newpass')
		if auth_user(username, oldp):
			set_password(username, newp)
	
	dirname = ''
	if 'dir' in req._GET:
		dirname = req._GET['dir'][-1].strip('/\\')

	filename = ''
	if 'file' in req._GET:
		filename = req._GET['file'][-1].strip('/\\')


	# Determine pretty names for folders, used in HTML output
	p_dirname = parentdir(dirname)
	s_dirname = softdir(dirname)

	# Create absolute path of file or folder, used for security below
	path = absjoin(
		config.file_root,
		username,
		dirname,
		filename,
	)

	# Protect us from writing to places we don't want
	try:
		safepath(path)
	except AssertionError as e:
		return e.message

	# Handle folder creation
	if 'newfolder' in req._POST:
		nfolder = req._POST.getvalue('newfolder')
		if app_create_folder(path, nfolder):
			req.redirect = '/?dir=' + dirname
			return

	# Handle file uploads
	if 'fileupload' in req._POST:
		files = req._POST['fileupload']
		if type(files) != list:
			files = [files]
		if files[-1].filename:
			if app_file_uploads(path, files):
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
		filelist = listdir(path)
		content = []
		# If we are in the root don't add a "parent" option
		if not path == absjoin(config.file_root, username):
			content.append(templates.parent(dirname=p_dirname, filename='..'))

		for f in filelist:
			if f[0]:
				content.append(templates.directory(dirname=os.path.join(dirname, f[1]), filename=f[1]))
			else:
				content.append(templates.file(dirname=dirname, filename=f[1]))

		return templates.index(
			title=os.sep if not dirname else dirname,
			username=username,
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
	application.run(port=8000)