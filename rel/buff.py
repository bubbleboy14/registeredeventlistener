"""
This module has a BuffWriter and a convenience function, buffwrite().
"""

from .rel import read, write, error, log

WMAX = 4096
writings = {}

class BuffWriter(object):
	def __init__(self, sock, data, sender=None, onerror=None):
		self.data = []
		self.sock = sock
		self.fileno = sock.fileno()
		self.sender = sender or sock.send
		self.onerror = onerror
		self.errors = 0
		self.listen()
		self.ingest(data)
		self.log("initialized with %s-part message"%(len(self.data),))

	def log(self, *msg):
		log("BuffWriter[%s]: %s"%(self.fileno, " ".join(msg)))

	def error(self):
		if self.onerror and not self.errors:
			self.onerror() # 1st time only...
		self.errors += 1
		self.log("error #%s"%(self.errors,))

	def write(self):
		if self.errors:
			return self.log("aborting write (errors!)")
		d = self.data[0]
		sent = self.sender(self.sock, d)
		if sent == len(d):
			self.data.pop(0)
		else:
			self.data[0] = d[sent:]
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
		writings[fn].ingest(data)
	else:
		writings[fn] = BuffWriter(sock, data, sender, onerror)
	