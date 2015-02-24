from Cookie import SimpleCookie
from clam import logger
from clam import config
from clam import hook
import hashlib


class defaultsession(hook.session):
	"""cookie based sesssion handler"""

	def __init__(self, request):
		self.req = request

	def set(self, username, expires=None):
		s = username + ":" + self.req._ENV.get('REMOTE_ADDR', '-')
		s_hash = hashlib.sha1(s + config.secret).hexdigest()

		session_cookie = SimpleCookie()
		session_cookie['clamsession'] = s + ":" + s_hash
		session_cookie['clamsession']["path"] = '/'
		session_cookie['clamsession']["httponly"] = True
		if expires:
			session_cookie['clamsession']["expires"] = expires
		self.req.headers += [("set-cookie", m.OutputString()) for m in session_cookie.values()]
		return True

	def expire(self):
		return self.set('-', 'Thu, 01 Jan 1970 00:00:00 GMT')

	def get(self):
		s = self.req._ENV.get('HTTP_COOKIE', None)
		if not s:
			return None
		session_cookie = SimpleCookie(s)

		if not 'clamsession' in session_cookie:
			return None

		username, remote, uhash = session_cookie['clamsession'].value.split(':')
		s_hash = hashlib.sha1(username + ":" + remote + config.secret).hexdigest()
		if uhash == s_hash:
			if remote == self.req._ENV.get('REMOTE_ADDR', '-'):
				return username