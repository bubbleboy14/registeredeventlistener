"""
This module contains three functions: emit(), ask(), and listen().

### listen(channel, cb)
This function registers a listener callback on a channel.

### emit(channel, *args, **kwargs)
This function emits an event to all listeners on a channel.

### ask(channel, *args, **kwargs)
This function requests an answer from the first registered listener
on a channel.
"""

listeners = {}

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