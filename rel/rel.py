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
from registrar import SelectRegistrar, PollRegistrar, EpollRegistrar
from listener import EV_PERSIST, EV_READ, EV_SIGNAL, EV_TIMEOUT, EV_WRITE
try:
    import event as pyevent
except:
    pyevent = None

registrar = None
threader = None
verbose = False
supported_methods = ['pyevent','epoll','poll','select']

mapping = {
    'select': SelectRegistrar,
    'epoll': EpollRegistrar,
    'poll': PollRegistrar,
}

def __display(text):
    if verbose:
        print "Registered Event Listener output:",text

def __report():
    print "=" * 60
    print "rel status report".center(60)
    print str(time.time()).center(60)
    print "-" * 60
    print "events".center(60)
    pprint.pprint(registrar.events)
    print "signals".center(60)
    pprint.pprint(registrar.signals)
    print "timers".center(60)
    pprint.pprint(registrar.timers)
    print "=" * 60
    return True

class Thread_Checker(object):
    def __init__(self):
        self.go()

    def go(self):
        if registrar == pyevent:
            self.checker = timeout(1,self.check)
            self.sleeper = timeout(0.01, self.release)
            self.sleeper.delete()

    def stop(self):
        if registrar == pyevent:
            self.checker.delete()
            self.sleeper.delete()

    def release(self, *args):
        time.sleep(.005)
        return True

    def check(self):
        if threading.activeCount() > 1:
            if not self.sleeper.pending():
                __display('Enabling GIL hack')
                self.sleeper.add(.01)
        else:
            if self.sleeper.pending():
                __display('Disabling GIL hack')
                self.sleeper.delete()
        return True

def check_init():
    if not registrar:
        initialize()

def get_registrar(method):
    if method == 'pyevent':
        if not pyevent:
            raise ImportError, "could not import event"
        return pyevent
    if method in mapping:
        return mapping[method]()
    raise ImportError

def initialize(methods=supported_methods,options=()):
    """
    initialize(methods=['pyevent','epoll','poll','select'],options=[])
    possible options:
        'verbose' - prints out certain events
        'report' - prints status of non-pyevent registrar every 5 seconds
    """
    global registrar
    global threader
    global verbose
    if "verbose" in options:
        verbose = True
    if "strict" not in options:
        for m in supported_methods:
            if m not in methods:
                methods.append(m)
    for method in methods:
        try:
            registrar = get_registrar(method)
            break
        except:
            __display('Could not import "%s"'%method)
    if registrar is None:
        raise ImportError, "Could not import any of given methods: %s" % (methods,)
    threader = Thread_Checker()
    if "report" in options and registrar != pyevent:
        timeout(5,__report)
    __display('Initialized with "%s"'%method)
    return method

def read(sock,cb,*args):
    check_init()
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
    check_init()
    registrar.dispatch()

def loop():
    check_init()
    registrar.loop()

def abort():
    check_init()
    registrar.abort()

def init():
    check_init()
    threader.stop()
    registrar.init()
    threader.go()

def event(callback,arg=None,evtype=0,handle=None):
    check_init()
    return registrar.event(callback,arg,evtype,handle)