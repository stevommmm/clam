import os
from string import Template as _tplt

template_root = os.path.dirname(os.path.abspath(__file__))

class TemplateManager(object):
	def __init__(self):
		self.templates = {}

	def add(self, template, ext=".html"):
		with open(os.path.join(template_root, template + ext)) as f:
			self.templates[template] = _tplt(f.read())

	def flatten(self, kwargs):
		def inner():
			for k,v in kwargs.iteritems():
				if type(v) in [list, set]:
					yield k, '\n'.join(v)
				else:
					yield k, v
		return dict(inner())

	def __getattr__(self, name):
		def inner(**kwargs):
			return self.templates[name].safe_substitute(**self.flatten(kwargs))
		if name in self.templates:
			return inner
		else:
			raise ValueError('Template not found')


templates = TemplateManager()

for x in os.listdir(template_root):
	filename, ext = os.path.splitext(x)
	if ext in ['.html', '.css', '.js']:
		templates.add(filename, ext)