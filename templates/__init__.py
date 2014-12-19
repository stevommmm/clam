import os
from string import Template as _tplt

template_root = os.path.dirname(os.path.abspath(__file__))

class Template(object):
	def __init__(self):
		self.templates = {}

	def add(self, template, ext=".html"):
		with open(os.path.join(template_root, template + ext)) as f:
			self.templates[template] = _tplt(f.read())

	def __getattr__(self, name):
		def inner(**kwargs):
			return self.templates[name].safe_substitute(**kwargs)
		# self.add(name)
		if name in self.templates:
			return inner
		else:
			raise ValueError('Template not found')

templates = Template()

for x in os.listdir(template_root):
	filename, ext = os.path.splitext(x)
	if ext in ['.html', '.css', '.js']:
		templates.add(filename, ext)