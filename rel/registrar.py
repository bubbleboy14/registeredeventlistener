from listener import Event, SocketIO, Timer, Signal, contains
import select, signal, time
try:
    import epoll
except ImportError:
    epoll = None

LISTEN_SELECT = 0#.001
LISTEN_POLL = 0#10
SLEEP_SEC = .001

def kbint(signals):
    if signal.SIGINT in signals:
        return True
    raise KeyboardInterrupt("You have not set a Keyboard Interrupt callback. To do so, use: 'rel.signal(2, your_callback_function)'.")

class Registrar(object):
    def __init__(self):
        self.events = {'read':{},'write':{}}
        self.timers = set()
        self.addlist = []
        self.rmlist = []
        self.signals = {}
        self.run_dispatch = False
        self.error_check = False

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
        tmp = SocketIO(self,'read',sock,cb,*args)
        self.add(tmp)
        return tmp

    def write(self,sock,cb,*args):
        tmp = SocketIO(self,'write',sock,cb,*args)
        self.add(tmp)
        return tmp

    def dispatch(self):
        self.run_dispatch = True
        while self.run_dispatch:
            if not self.loop():
                self.run_dispatch = False

    def loop(self):
        time.sleep(SLEEP_SEC)
        e = self.check_events()
        t = self.check_timers()
        return e or t or self.signals

    def abort(self):
        self.run_dispatch = False
        for ev_list in self.events.values():
            for sockio in ev_list.values():
                sockio.sock.close()

    def signal(self,sig,cb,*args):
        return Signal(self,sig,cb,*args)

    def timeout(self,delay,cb,*args):
        return Timer(self,delay,cb,*args)

    def add_timer(self, timer):
         self.addlist.append(timer)

    def remove_timer(self, timer):
        self.rmlist.append(timer)

    def check_timers(self):
        for timer in self.addlist:
            self.timers.add(timer)
        self.addlist = []
        for timer in self.rmlist:
            if timer in self.timers:
                self.timers.remove(timer)
        self.rmlist = []
        for timer in self.timers:
            if not timer.check():
                self.rmlist.append(timer)
        return bool(self.timers)

    def handle_error(self, fd):
        if fd in self.events['read']:
            self.events['read'][fd].callback()
        if fd in self.events['write']:
            self.events['write'][fd].callback()

class SelectRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)

    def add(self, event):
        self.events[event.evtype][event.fd] = event

    def remove(self, event):
        if event.fd in self.events[event.evtype]:
            del self.events[event.evtype][event.fd]

    def check_events(self):
        if self.events['read'] or self.events['write']:
            rlist = self.events['read'].keys()
            wlist = self.events['write'].keys()
            try:
                r,w,e = select.select(rlist,wlist,rlist+wlist,LISTEN_SELECT)
            except select.error:
                return kbint(self.signals)
            for fd in r:
                self.events['read'][fd].callback()
            for fd in w:
                self.events['write'][fd].callback()
            for fd in e:
                self.handle_error(fd)
            return True
        return False

class PollRegistrar(Registrar):
    def __init__(self):
        Registrar.__init__(self)
        try:
            self.poll = select.poll()
        except AttributeError:
            # Probably a platform without poll support, such as Windows
            raise ImportError, "could not import poll"

    def add(self, event):
        self.events[event.evtype][event.fd] = event
        self.register(event.fd)

    def remove(self, event):
        if event.fd in self.events[event.evtype]:
            del self.events[event.evtype][event.fd]
            self.poll.unregister(event.fd)
            self.register(event.fd)

    def check_events(self):
        if self.events['read'] or self.events['write']:
            try:
                items = self.poll.poll(LISTEN_POLL)
            except select.error:
                return kbint(self.signals)
            except epoll.error:
                return kbint(self.signals)
            for fd,etype in items:
                if contains(etype,select.POLLIN) and fd in self.events['read']:
                    self.events['read'][fd].callback()
                if contains(etype,select.POLLOUT) and fd in self.events['write']:
                    self.events['write'][fd].callback()
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
        if mode:
            try:
                self.poll.register(fd, mode)
            except epoll.error:
                pass

class EpollRegistrar(PollRegistrar):
    def __init__(self):
        if epoll is None:
            raise ImportError, "could not import epoll"
        Registrar.__init__(self)
        self.poll = epoll.poll()
