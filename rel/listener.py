import time
import signal

EV_PERSIST = 16
EV_READ = 2
EV_SIGNAL = 8
EV_TIMEOUT = 1
EV_WRITE = 4
noadd = "this is a do-not-add order from your mother, an Event object"

def contains(mode,bit):
    return mode&bit==bit

class Event(object):
    def __init__(self,registrar,cb,arg,evtype,handle):
        self.registrar = registrar
        self.cb = cb
        self.arg = arg
        self.timeout = self.registrar.timeout(None,self.callback)
        self.evtype = evtype or 1
        self.handle = handle
        self.children = []
        self.spawn_children()

    def spawn_children(self):
        persist = contains(self.evtype,EV_PERSIST)
        if contains(self.evtype,EV_SIGNAL):
            self.children.append(self.registrar.signal(self.handle,self.callback,noadd))
        if contains(self.evtype,EV_READ):
            tmp = self.registrar.read(self.handle,self.callback,noadd)
            if persist:
                tmp.persistent()
            self.children.append(tmp)
        if contains(self.evtype,EV_WRITE):
            tmp = self.registrar.write(self.handle,self.callback,noadd)
            if persist:
                tmp.persistent()
            self.children.append(tmp)

    def add(self, delay=None):
        if delay is not None:
            self.timeout.add(delay)
        for child in self.children:
            child.add()

    def delete(self):
        self.timeout.delete()
        for child in self.children:
            child.delete()

    def pending(self):
        for child in self.children:
            if child.pending():
                return 1
        return self.timeout.pending()

    def callback(self):
        self.cb(self,self.handle,self.evtype,self.arg)

class SocketIO(object):
    def __init__(self, registrar, evtype, sock, cb, *args):
        self.registrar = registrar
        self.evtype = evtype
        self.sock = sock
        self.fd = sock
        if hasattr(self.fd,'fileno'):
            self.fd = self.fd.fileno()
        self.cb = cb
        self.args = args
        self.persist = False
        self.active = 0
        if noadd in self.args:
            self.args = ()
            return
        self.timeout = self.registrar.timeout(None,self.callback)
        self.add()

    def __repr__(self):
        cbname = self.cb.__name__
        if hasattr(self.cb,"im_class"):
            cbname = self.cb.__self__.__class__.__name__ + "." + cbname
        return '<SocketIO Object | Callback:"%s">'%cbname

    def persistent(self):
        self.persist = True

    def add(self, delay=None):
        if delay is not None:
            self.timeout.add(delay)
        self.registrar.add(self)
        self.active = 1

    def delete(self):
        self.registrar.remove(self)
        self.active = 0

    def dereference(self):
        if self.pending():
            self.delete()
        self.cb = None
        self.args = None
        self.timeout.delete(True)

    def pending(self):
        return self.active

    def callback(self):
        if not self.cb(*self.args) and not self.persist and self.active:
            self.delete()

class Signal(object):
    def __init__(self, registrar, sig, cb, *args):
        self.registrar = registrar
        self.sig = sig
        self.default = signal.getsignal(self.sig)
        self.cb = cb
        self.args = args
        if noadd in self.args:
            self.args = ()
            return
        self.timeout = self.registrar.timeout(None,self.callback)
        self.add()

    def __repr__(self):
        cbname = self.cb.__name__
        if hasattr(self.cb,"im_class"):
            cbname = self.cb.__self__.__class__.__name__ + "." + cbname
        return '<Signal Object | Callback:"%s">'%cbname

    def add(self, delay=None):
        if delay is not None:
            self.timeout.add(delay)
        signal.signal(self.sig,self.callback)
        self.active = 1
        self.registrar.signal_add(self)

    def delete(self):
        self.reset()
        self.active = 0
        self.registrar.signal_remove(self.sig)

    def reset(self):
        signal.signal(self.sig,self.default)

    def pending(self):
        return self.active

    def callback(self,*args):
        self.cb(*self.args)
        self.registrar.error_check = True

class Timer(object):
    def __init__(self, registrar, delay, cb, *args):
        self.registrar = registrar
        self.cb = cb
        self.args = args
        if noadd in self.args:
            self.args = ()
            return
        self.add(delay)

    def __repr__(self):
        cbname = self.cb.__name__
        if hasattr(self.cb,"im_class"):
            cbname = self.cb.__self__.__class__.__name__ + "." + cbname
        return '<Timer Object | Callback:"%s">'%cbname

    def add(self, delay=None):
        self.delay = delay
        self.expiration = None
        if self.delay is not None:
            self.expiration = time.time()+self.delay
            self.registrar.add_timer(self)

    def delete(self, dereference=False):
        self.expiration = None
        self.registrar.remove_timer(self)
        if dereference:
            self.cb = None
            self.args = None

    def pending(self):
        if self.expiration:
            return 1
        return 0

    def check(self, t=None):
        if not self.pending():
            return False
        if (t or time.time()) >= self.expiration:
            if self.cb(*self.args):
                self.add(self.delay)
                return True
            return False
        return True