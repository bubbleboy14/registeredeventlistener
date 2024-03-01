"""
This module contains five functions: emit(), ask(), listen(),
when(), and transpire().

### listen(channel, cb)
This function registers a listener callback on a channel.

### emit(channel, *args, **kwargs)
This function emits an event to all listen()ers on a channel.

### ask(channel, *args, **kwargs)
This function requests an answer from the first registered
listen()er on a channel.

### when(event, cb, *args, **kwargs)
This function calls cb if an event has transpire()d or
registers it to be called the first time it transpire()s.

### transpire(event)
This function triggers any when()-registered event
listeners, and notes that the event has transpired.
"""

listeners = {}
happenings = {}

def emit(channel, *args, **kwargs): # all cbs called, no return value
	if channel not in listeners:
		return print("%s: no one's listening"%(channel,))
	for cb in listeners[channel]:
		cb(*args, **kwargs)

def ask(channel, *args, **kwargs): # only 1st cb called, data returned
	if channel not in listeners:
		return print("%s: no one's listening"%(channel,))
	for cb in listeners[channel]:
		return cb(*args, **kwargs)

def listen(channel, cb):
	if channel not in listeners:
		listeners[channel] = []
	listeners[channel].append(cb)

def when(event, cb, *args, **kwargs):
	if event not in happenings:
		happenings[event] = []
	if happenings[event] == "transpired":
		cb(*args, **kwargs)
	else:
		happenings[event].append([cb, args, kwargs])

def transpire(event):
	if event in happenings:
		if happenings[event] == "transpired":
			return
		for cb, args, kwargs in happenings[event]:
			cb(*args, **kwargs)
	happenings[event] = "transpired"