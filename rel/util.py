import os, json, base64

def log(*msg):
	print(*msg)

def read(fname):
	if not os.path.exists(fname):
		return
	f = open(fname, 'r')
	data = f.read()
	f.close()
	return data and json.loads(base64.b64decode(data).decode())

def write(fname, data):
	f = open(fname, 'w')
	f.write(base64.b64encode(json.dumps(data).encode()).decode())
	f.close()

membank = {}
remembered = read(".membank")
remembered and membank.update(remembered)

def remember(key, data, ask=True):
	if ask and input("remember %s for next time? [Y/n] "%(key,)).lower().startswith("n"):
		return log("ok, not remembering", key)
	membank[key] = data
	write(".membank", membank)

def recall(key):
	return membank.get(key, None)

def memget(key, default=None):
	val = recall(key)
	if not val:
		pstr = "%s? "%(key,)
		if default:
			pstr = "%s[default: %s] "%(pstr, default)
		val = input(pstr) or default
		remember(key, val)
	return val

listeners = {}
def emit(channel, *data): # all cbs called, no return value
	if channel not in listeners:
		return log("%s: no one's listening"%(channel,))
	for cb in listeners[channel]:
		cb(*data)

def ask(channel, *data): # only 1st cb called, data returned
	if channel not in listeners:
		return log("%s: no one's listening"%(channel,))
	for cb in listeners[channel]:
		return cb(*data)

def listen(channel, cb):
	if channel not in listeners:
		listeners[channel] = []
	listeners[channel].append(cb)