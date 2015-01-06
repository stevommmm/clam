from clam import hook
from clam import config
from clam import logger
from clam import util

from Cookie import SimpleCookie
import hashlib
import os

def hashcs(s):
	return hashlib.sha1(s + config.secret).hexdigest()

def default_set_session(req, username, expires=None):
	s = username + ":" + req._ENV.get('REMOTE_ADDR', '-')
	s_hash = hashlib.sha1(s + config.secret).hexdigest()

	session_cookie = SimpleCookie()
	session_cookie['clamsession'] = s + ":" + s_hash
	session_cookie['clamsession']["path"] = '/'
	session_cookie['clamsession']["httponly"] = True
	if expires:
		session_cookie['clamsession']["expires"] = expires
	req.headers += [("set-cookie", m.OutputString()) for m in session_cookie.values()]

def default_get_session(req):
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

def default_auth_user(req, username, password):
	pwh = hashcs(password)
	pwf = util.absjoin(config.file_root, username, '.password')
	if util.safepath(pwf):
		return pwh.strip() == open(pwf, 'rb').read().strip()
	return False

def default_set_password(username, password):
	pwh = hashcs(password)
	pwf = os.path.join(config.file_root, username, '.password')
	if util.safepath(pwf):
		with open(pwf, 'wb') as f:
			f.write(pwh)




hook.register('set_session', default_set_session)
hook.register('get_session', default_get_session)
hook.register('verify_user_password', default_auth_user)
hook.register('set_user_password', default_set_password)