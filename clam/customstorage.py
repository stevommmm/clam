import cgi
import os

class ClamFieldStorage(cgi.FieldStorage):
	def __init__(self, fp=None, headers=None, outerboundary="", environ=os.environ, keep_blank_values=0, strict_parsing=0):
		cgi.FieldStorage.__init__(self, fp, headers, outerboundary, environ, keep_blank_values, strict_parsing)

	def make_file(self, binary=None):
		print 'tempcreate'
		import tempfile
		return tempfile.TemporaryFile("w+b")

	def __repr__(self):
		return "FieldStorage(%r, %r, ...)" % ( self.name, self.filename)
