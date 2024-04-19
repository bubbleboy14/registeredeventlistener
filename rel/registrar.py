"""
This module includes the Registrar class and four subclasses,
KqueueRegistrar, SelectRegistrar, PollRegistrar, and EpollRegistrar,
each of which utilizes a different subsystem (kqueue, select, poll,
or epoll) to manage read and write events. Registrar and its subclasses
also manage signals and timers.

### Reads and Writes
Reads and writes are handled by the SocketIO class defined in the
listener module, which is instantiated by a couple Registrar functions:

    def read(self,sock,cb,*args):
        return SocketIO(self,'read',sock,cb,*args)

    def write(self,sock,cb,*args):
        return SocketIO(self,'write',sock,cb,*args)

### Signals and Timers
Signals and timers are handled by the Signal and Timer classes
defined in the listener module, which can be instantiated through
a couple Registrar functions:

    def signal(self,sig,cb,*args):
        return Signal(self,sig,cb,*args)

    def timeout(self,delay,cb,*args):
        return Timer(self,delay,cb,*args)

The Registrar API is taken from [pyevent](https://github.com/jaraco/pyevent),
which is a wrapper around [libevent](http://monkey.org/~provos/libevent/).

Note that while rel can be configured to use pyevent under the hood
(instead of one of the Registrar subclasses), such usage forfeits
various benefits of the pure-Python Registrar subclasses, including
GIL integration / thread compatibility.

### Event Engine Rates
Another benefit of the pure-Python Registrar subclasses (wrapping epoll,
poll, kqueue, and select - by default, rel uses the fastest available) is
that they run at configurable rates. By default, rel's CPU footprint is
unnoticeably tiny unless it's currently managing active writes, in which
case it ramps up to push the bytes through faster. These rates (normal
and turbo) can be adjusted with a couple functions:

    def set_sleep(s):
        global SLEEP_SEC
        SLEEP_SEC = s

    def set_turbo(s):
        global SLEEP_TURBO
        SLEEP_TURBO = s
"""

from datetime import datetime
from .listener import Event, SocketIO, Timer, Signal, contains
from .errors import AbortBranch
import select, signal, time, operator
try:
    from select import epoll
except ImportError:
    epoll = None

LISTEN_KQUEUE = 0
LISTEN_SELECT = 0
LISTEN_POLL = 0
SLEEP_SEC = .03
SLEEP_TURBO = 0.0001
SEL_MAX_FD = 256

def set_sleep(s):
    global SLEEP_SEC
    SLEEP_SEC = s

def set_turbo(s):
    global SLEEP_TURBO
    SLEEP_TURBO = s

def kbint(signals):
    if signal.SIGINT in signals:
        return True
    raise KeyboardInterrupt("You have not set a Keyboard Interrupt callback. To do so, use: 'rel.signal(2, your_callback_function)'.")

class Registrar(object):
    def __init__(self):
        self.events = {'read':{},'write':{},'error':{}}
        self.timers = []
        self.addlist = []
        self.rmlist = []
        self.signals = {}
        self.tick = 0
        self.run_dispatch = False
        self.error_check = False

    def report(self):
        return {
            "timers": len(self.timers),
            "signals": len(list(self.signals.keys())),
            "reads": len(list(self.events["read"].keys())),
            "writes": len(list(self.events["write"].keys()))
        }

    def signal_add(self, sig):
        self.signals[sig.sig] = sig

    def signal_remove(self, sig):
        if sig in self.signals:
            del self.signals[sig]

    def init(self):
        for sig in self.signals:
            self.signals[sig].reset()
        self.__init__()

    def event(self,callback,arg,evtype,handle):
        return Event(self,callback,arg,evtype,handle)

    def read(self,sock,cb,*args):
        return SocketIO(self,'read',sock,cb,*args)

    def write(self,sock,cb,*args):
        return SocketIO(self,'write',sock,cb,*args)

    def error(self,sock,cb,*args):
        return SocketIO(self,'error',sock,cb,*args)

    def dispatch(self):
        self.run_dispatch = True
        while self.run_dispatch:
            if not self.loop():
                self.run_dispatch = False

    def loop(self):
        if SLEEP_TURBO and self.events["write"]:
            time.sleep(SLEEP_TURBO)
        else:
            time.sleep(SLEEP_SEC)
        self.tick = datetime.now().microsecond
        e = self.check_events()
        t = self.check_timers()
        return e or t or self.signals

    def abort(self):
        self.run_dispatch = False
        for ev_list in list(self.events.values()):
            for sockio in list(ev_list.values()):
                sockio.delete()

    def abort_branch(self):
        raise AbortBranch()

    def signal(self,sig,cb,*args):
        return Signal(self,sig,cb,*args)

    def timeout(self,delay,cb,*args):
        return Timer(self,delay,cb,*args)

    def add_timer(self, timer):
         self.addlist.append(timer)

    def remove_timer(self, timer):
        self.rmlist.append(timer)

    def check_timers(self):
        changes = len(self.addlist) or len(self.rmlist)
        for timer in self.addlist:
            if timer not in self.timers:
                self.timers.append(timer)
        self.addlist = []
        for timer in self.rmlist:
            if timer in self.timers:
                self.timers.remove(timer)
        self.rmlist = []
        changes and self.timers.sort(key=operator.attrgetter("expiration"))
        t = time.time()
        for timer in self.timers:
            if not timer.check(t):
                self.rmlist.append(timer)
        return bool(self.timers)

    def callback(self, etype, fd):
        try:
            self.events[etype][fd].callback()
        except AbortBranch as e:
            pass # just go on with other code :)

    def handle_error(self, fd):
        if fd in self.events['error']:
            self.callback('error', fd)

    def handle_error_nah(self, fd):
        if fd in self.events['read']:
            self.callback('read', fd)
        if fd in self.events['write']:
            self.callback('write', fd)

class KqueueRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)
        if not hasattr(select, "kqueue"):
            raise ImportError("could not find kqueue -- need Python 2.6+ on BSD (including OSX)!")
        self.kq = select.kqueue()
        self.kqf = {
            "read": select.KQ_FILTER_READ,
            "write": select.KQ_FILTER_WRITE
        }

    def abort(self):
        Registrar.abort(self)
        self.kq.close()
    
    def add(self, event):
        self.events[event.evtype][event.fd] = event
        if event.evtype != "error": # comes in as a write...
            self.kq.control([select.kevent(event.fd, self.kqf[event.evtype], select.KQ_EV_ADD)], 0)
    
    def remove(self, event):
        if event.fd in self.events[event.evtype]:
            del self.events[event.evtype][event.fd]
            try:
                self.kq.control([select.kevent(event.fd, self.kqf[event.evtype], select.KQ_EV_DELETE)], 0)
            except Exception as e:
                pass #connection probably closed
    
    def check_events(self):
        if self.events['read'] or self.events['write']:
            elist = self.kq.control(None, 1000, LISTEN_KQUEUE)
            for e in elist:
                if e.filter == self.kqf['read']:
                    self.callback('read', e.ident)
                elif e.filter == self.kqf['write']:
                    if e.flags & select.KQ_EV_EOF:
                        self.handle_error(e.ident)
                    else:
                        self.callback('write', e.ident)
                else:
                    self.handle_error(e.ident)
            return True
        return False

class SelectRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)

    def add(self, event):
        self.events[event.evtype][event.fd] = event

    def remove(self, event):
        if event.fd in self.events[event.evtype]:
            del self.events[event.evtype][event.fd]

    def do_check(self, rlist, wlist):
        try:
            r,w,e = select.select(rlist,wlist,rlist+wlist,LISTEN_SELECT)
        except select.error:
            return kbint(self.signals)
        for fd in r:
            self.callback('read', fd)
        for fd in w:
            self.callback('write', fd)
        for fd in e:
            self.handle_error(fd)
        return True

    def check_events(self):
        success = False
        if self.events['read'] or self.events['write']:
            rlist = list(self.events['read'].keys())
            wlist = list(self.events['write'].keys())
            longest = max(len(rlist), len(wlist))
            s = 0
            while s < longest:
                e = s + SEL_MAX_FD
                success = self.do_check(rlist[s:e], wlist[s:e]) or success
                s = e
        return success

class PollRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)
        try:
            self.poll = select.poll()
        except AttributeError:
            # Probably a platform without poll support, such as Windows
            raise ImportError("could not import poll")

    def add(self, event):
        self.events[event.evtype][event.fd] = event
        self.register(event.fd)

    def remove(self, event):
        if event.fd in self.events[event.evtype]:
            del self.events[event.evtype][event.fd]
            try:
                self.poll.unregister(event.fd)
            except OSError:
                pass # this shouldn't happen....
            self.register(event.fd)

    def check_events(self):
        if self.events['read'] or self.events['write']:
            try:
                items = self.poll.poll(LISTEN_POLL)
            except select.error:
                return kbint(self.signals)
            for fd,etype in items:
                if contains(etype,select.POLLIN) and fd in self.events['read']:
                    self.callback('read', fd)
                if contains(etype,select.POLLOUT) and fd in self.events['write']:
                    self.callback('write', fd)
                if contains(etype,select.POLLERR) or contains(etype,select.POLLHUP):
                    self.handle_error(fd)
            return True
        return False

    def register(self, fd):
        mode = 0
        if fd in self.events['read']:
            mode = mode|select.POLLIN
        if fd in self.events['write']:
            mode = mode|select.POLLOUT
        if fd in self.events['error']:
            mode = mode|select.POLLERR
        if mode:
            try:
                self.poll.register(fd, mode)
            except select.error:
                try:
                    self.poll.modify(fd, mode)
                except:
                    self.handle_error(fd)

class EpollRegistrar(PollRegistrar):
    def __init__(self):
        if epoll is None:
            raise ImportError("could not import epoll")
        Registrar.__init__(self)
        self.poll = epoll()
