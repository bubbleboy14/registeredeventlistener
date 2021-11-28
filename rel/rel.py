"""
R.E.L.
Registed Event Listener
module that uses various methods to emulate event-like behavior
functions:
    read(socket, callback, *args)
    write(socket, callback, *args)
    timeout(delay, callback, *args)
    signal(sig, callback, *args)
    event(callback,arg=None,evtype=0,handle=None)
    dispatch()
    loop()
    abort()
    init()
"""
import sys, threading, time, pprint
from .registrar import set_sleep, SelectRegistrar, PollRegistrar, EpollRegistrar, KqueueRegistrar
from .listener import EV_PERSIST, EV_READ, EV_SIGNAL, EV_TIMEOUT, EV_WRITE
try:
    import event as pyevent
except ImportError:
    pyevent = None

def override():
    if 'event' in sys.modules and sys.modules['event'].__class__.__name__ == "fakemodule":
        return
    class fakemodule(object):
        def __init__(self, **kwargs):
            for key, val in list(kwargs.items()):
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

running = False
registrar = None
threader = None
verbose = False
supported_methods = ['epoll','poll','kqueue','select','pyevent']

mapping = {
    'select': SelectRegistrar,
    'epoll': EpollRegistrar,
    'poll': PollRegistrar,
    'kqueue': KqueueRegistrar
}

def _display(text):
    if verbose:
        print("Registered Event Listener output:", text)

def __report():
    print("=" * 60)
    print("rel status report".center(60))
    print(str(time.time()).center(60))
    print("-" * 60)
    print("events".center(60))
    pprint.pprint(registrar.events)
    print("signals".center(60))
    pprint.pprint(registrar.signals)
    print("timers".center(60))
    pprint.pprint(registrar.timers)
    print("=" * 60)
    return True

class Thread_Checker(object):
    def __init__(self, threaded):
        self.active = threaded and registrar == pyevent
        if threaded and registrar != pyevent:
            _display('GIL hack unnecessary for non-pyevent registrar. GIL hack disabled.')
        self.go()

    def go(self):
        if self.active:
            _display('Thread Checking Enabled')
            self.checker = timeout(1,self.check)
            self.sleeper = timeout(0.01, self.release)
            self.sleeper.delete()

    def stop(self):
        if self.active:
            _display('Thread Checking Disabled')
            self.checker.delete()
            self.sleeper.delete()

    def release(self, *args):
        time.sleep(.005)
        return True

    def check(self):
        if threading.activeCount() > 1:
            if not self.sleeper.pending():
                _display('Enabling GIL hack')
                self.sleeper.add(.01)
        else:
            if self.sleeper.pending():
                _display('Disabling GIL hack')
                self.sleeper.delete()
        return True

def check_init():
    if not registrar:
        initialize()

def get_registrar(method):
    if method == 'pyevent':
        if not pyevent:
            raise ImportError("could not import event")
        return pyevent
    if method in mapping:
        return mapping[method]()
    raise ImportError

def initialize(methods=supported_methods,options=()):
    """
    initialize(methods=['epoll','poll','kqueue','select','pyevent'],options=[])
    possible options:
        'verbose' - prints out certain events
        'report' - prints status of non-pyevent registrar every 5 seconds
        'strict' - ONLY try specified methods
        'threaded' - enable GIL hack -- pyevent only!
    """
    global registrar
    global threader
    global verbose
    verbose = "verbose" in options
    if "strict" not in options:
        for m in supported_methods:
            if m not in methods:
                methods.append(m)
    for method in methods:
        try:
            registrar = get_registrar(method)
            break
        except ImportError:
            _display('Could not import "%s"'%method)
    if registrar is None:
        raise ImportError("Could not import any of given methods: %s" % (methods,))
    _display('Initialized with "%s"'%method)
    threader = Thread_Checker('threaded' in options)
    if "report" in options:
        if registrar == pyevent:
            _display('Reporting disabled in pyevent. Choose epoll, poll, or select to enable reporting.')
        else:
            timeout(5,__report)
    return method

SAFE_READ = False
def safe_read():
    global SAFE_READ
    SAFE_READ = True

def read(sock,cb,*args):
    check_init()
    if SAFE_READ:
        return registrar.read(sock,cb)
    return registrar.read(sock,cb,*args)

def write(sock,cb,*args):
    check_init()
    return registrar.write(sock,cb,*args)

def timeout(delay, cb, *args):
    check_init()
    return registrar.timeout(delay,cb,*args)

def signal(sig, callback, *args):
    check_init()
    return registrar.signal(sig,callback,*args)

def dispatch():
    global running
    if not running:
        running = True
        check_init()
        registrar.dispatch()

def loop():
    check_init()
    registrar.loop()

def report():
    check_init()
    return registrar.report()

def abort():
    global running
    running = False
    check_init()
    registrar.abort()

def abort_branch():
    check_init()
    registrar.abort_branch()

def init():
    global running
    running = False
    check_init()
    threader.stop()
    registrar.init()
    threader.go()

def event(callback,arg=None,evtype=0,handle=None):
    check_init()
    return registrar.event(callback,arg,evtype,handle)

def _thread_wrapper(callback):
    from .errors import AbortBranch
    try:
        callback()
    except AbortBranch as e:
        pass # we don't care at this point

def thread(callback):
    threading.Thread(target=_thread_wrapper, args=(callback,)).start()

def tick():
    check_init()
    return registrar.tick