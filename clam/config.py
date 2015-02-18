import os

class config:
	root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
	file_root = os.path.join(root, 'data') + os.sep
	tmp_root = os.path.join(root, 'tmp') + os.sep
	secret = 'supersecretstring'

if not os.path.exists(config.file_root):
	os.mkdir(config.file_root)
if not os.path.exists(config.tmp_root):
	os.mkdir(config.tmp_root)