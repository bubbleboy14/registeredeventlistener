"""
This module has a BuffWriter and a convenience function, buffwrite().
"""

from .rel import read, write, error, log

WMAX = 4096
writings = {}

class BuffWriter(object):
	def __init__(self, sock, data, sender=None, onerror=None):
		self.data = []
		self.errors = []
		self.sock = sock
		self.fileno = sock.fileno()
		self.sender = sender or sock.send
		if not onerror:
			onerror = lambda *a : self.log("unhandled error:", *a)
		self.onerror = onerror
		self.listen()
		self.ingest(data)
		self.log("initialized with %s-part message"%(len(self.data),))

	def log(self, *msg):
		log("BuffWriter[%s]: %s"%(self.fileno, " ".join(msg)))

	def error(self, msg="unexpected error"):
		self.onerror(msg)
		self.errors.append(msg)
		self.log("error #%s: %s"%(len(self.errors), msg))

	def write(self):
		try:
			self.sender(self.sock, self.data[0])
		except Exception as e:
			self.data = []
			return self.error("write error: %s"%(e,))
		self.data.pop(0)
		self.data or self.log("write complete")
		return self.data

	def listen(self):
		self.log("listening")
		self.listeners = {
			"error": error(self.sock, self.error),
			"write": write(self.sock, self.write)
		}

	def ingest(self, data):
		self.log("ingesting %s bytes"%(len(data),))
		while data:
			self.data.append(data[:WMAX])
			data = data[WMAX:]
		for etype in self.listeners:
			self.listeners[etype].pending() or self.listeners[etype].add()

def buffwrite(sock, data, sender, onerror):
	fn = sock.fileno()
	if fn in writings:
		writings[fn].sock = sock
		writings[fn].ingest(data)
	else:
		writings[fn] = BuffWriter(sock, data, sender, onerror)
	