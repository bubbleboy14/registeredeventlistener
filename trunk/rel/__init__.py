__version__ = "0.2.6.1"
from rel import supported_methods, initialize, read, write, timeout, signal, event, dispatch, loop, abort, init, sys, EV_PERSIST, EV_READ, EV_SIGNAL, EV_TIMEOUT, EV_WRITE

def override():
    if 'event' in sys.modules and sys.modules['event'].__class__.__name__ == "fakemodule":
        return
    class fakemodule(object):
        def __init__(self, **kwargs):
            for key, val in kwargs.items():
                setattr(self, key, val)
    pyevent_03_keys = [
        'EV_PERSIST',
        'EV_READ',
        'EV_SIGNAL',
        'EV_TIMEOUT',
        'EV_WRITE',
        '__author__',
        '__builtins__',
        '__copyright__',
        '__doc__',
        '__event_exc',
        '__file__',
        '__license__',
        '__name__',
        '__url__',
        '__version__',
        'abort',
        'dispatch',
        'event',
        'init',
        'loop',
        'read',
        'signal',
        'sys',
        'timeout',
        'write'
    ]
    kw = {}
    for key in pyevent_03_keys:
        kw[key] = globals().get(key, None)
    fakeevent = fakemodule(**kw)
    sys.modules['event'] = fakeevent
