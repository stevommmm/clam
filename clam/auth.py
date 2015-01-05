from Cookie import SimpleCookie
import hashlib
import os
from clam.config import config
from clam.fs import safepath

def hashcs(s):
	return hashlib.sha1(s + config.secret).hexdigest()

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
	pwh = hashcs(password)
	pwf = os.path.join(config.file_root, username, '.password')
	if safepath(pwf):
		return pwh.strip() == open(pwf, 'rb').read().strip()
	return False

def set_password(username, password):
	pwh = hashcs(password)
	pwf = os.path.join(config.file_root, username, '.password')
	if safepath(pwf):
		with open(pwf, 'wb') as f:
			f.write(pwh)

