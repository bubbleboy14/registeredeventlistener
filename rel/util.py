listeners = {}

def emit(channel, *data): # all cbs called, no return value
	if channel not in listeners:
		return print("%s: no one's listening"%(channel,))
	for cb in listeners[channel]:
		cb(*data)

def ask(channel, *data): # only 1st cb called, data returned
	if channel not in listeners:
		return print("%s: no one's listening"%(channel,))
	for cb in listeners[channel]:
		return cb(*data)

def listen(channel, cb):
	if channel not in listeners:
		listeners[channel] = []
	listeners[channel].append(cb)