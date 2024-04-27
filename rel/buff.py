"""
This module has a BuffWriter and a convenience function, buffwrite().
"""

from .rel import read, write, error, log

WMAX = 4096
writings = {}

class BuffWrite(object):
	def __init__(self, data, sender):
		self.data = []
		self.sender = sender
		self.complete = False
		self.error = None
		self.ingest(data)
		self.reset()

	def log(self, *msg):
		log("BuffWrite: %s"%(" ".join(msg),))

	def reset(self):
		self.position = 0

	def write(self, sock):
		try:
			self.sender(sock, self.data[self.position])
		except Exception as e:
			self.error = e
			return self.reset()
		self.position += 1
		if self.position == len(self.data):
			self.complete = True
			self.log("write complete")

	def ingest(self, data):
		while data:
			self.data.append(data[:WMAX])
			data = data[WMAX:]
		self.log("ingesting %s bytes -> %s chunks in buffer"%(len(data), len(self.data)))

class BuffWriter(object):
	def __init__(self, sock, data, sender=None, onerror=None):
		self.writes = []
		self.errors = []
		self.sock = sock
		self.fileno = sock.fileno()
		self.sender = sender or sock.send
		if not onerror:
			onerror = lambda *a : self.log("unhandled error:", *a)
		self.onerror = onerror
		self.listen()
		self.ingest(data)
		self.log("initialized with %s-byte message"%(len(data),))

	def log(self, *msg):
		log("BuffWriter[%s]: %s"%(self.fileno, " ".join(msg)))

	def error(self, msg="unexpected error"):
		self.onerror(msg)
		self.errors.append(msg)
		self.log("error #%s: %s"%(len(self.errors), msg))

	def write(self):
		bw = self.writes[0]
		bw.write(self.sock)
		if bw.error:
			return self.error("write error: %s"%(e,))
		bw.complete and self.writes.pop(0)
		self.writes or self.log("all writes complete")
		return self.writes

	def listen(self):
		self.log("listening")
		self.listeners = {
			"error": error(self.sock, self.error),
			"write": write(self.sock, self.write)
		}

	def ingest(self, data):
		self.log("ingesting %s bytes"%(len(data),))
		self.writes.append(BuffWrite(data, self.sender))
		for etype in self.listeners:
			self.listeners[etype].pending() or self.listeners[etype].add()

def buffwrite(sock, data, sender, onerror):
	fn = sock.fileno()
	if fn in writings:
		writings[fn].sock = sock
		writings[fn].ingest(data)
	else:
		writings[fn] = BuffWriter(sock, data, sender, onerror)
	