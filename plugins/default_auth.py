from clam import hook
from clam import config
from clam import logger
from clam import util

import hashlib
import os

def hashcs(s):
	return hashlib.sha256(s + config.secret).hexdigest()

class default_auth(hook.authentication):

	def __init__(self, username):
		self.username = username
		self.pwf = os.path.abspath(os.path.join(config.file_root, username, '.password'))
		assert self.pwf.startswith(config.file_root), "Invalid path"

	def password_verify(self, password):
		if not os.path.exists(self.pwf):
			return False
		pwh = hashcs(password)
		try:
			return pwh.strip() == open(self.pwf, 'rb').read().strip()
		except AssertionError, IOError:
			pass
		return False

	def password_set(self, password):
		try:
			with open(self.pwf, 'wb') as f:
				f.write(pwh)
		except IOError:
			pass
