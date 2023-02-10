# rel

More and more applications are coming to rely on pyevent. The problem is that pyevent itself requires compiling external modules and therefore presents a deployment hurdle. The rel module is a drop-in replacement for pyevent that completely emulates pyevent's interface, behavior and functionality on any system with Python. It can use pyevent if preferred/available, and otherwise rel will use the fastest method supported by the system. Epoll, poll, kqueue, and select are currently implemented.

### Get rel
Install rel with pip:

    pip3 install rel

### Basic Structure
The listener module contains classes for handling individual events. Instances
of these classes are managed by the Registrar subclasses (defined in the registrar
module).

The core rel module contains functions for selecting and initializing a Registrar
subclass, as well as user-facing functions (such as read(), write(), signal(), and
timeout()), which utilize said instance.

### Examples
Usage examples can be found throughout a rel-based asynchronous network library
called [dez](https://github.com/bubbleboy14/dez). Note that since dez originally
used pyevent, the rel functions are referenced throughout dez under the event
module, e.g. event.dispatch() instead of rel.dispatch(). This all works out due
to the dez [init file](https://github.com/bubbleboy14/dez/blob/master/dez/__init__.py) calling rel.override():

    import rel
    rel.override()

This enables a pyevent-based application (such as dez) to instead run on rel
without the need to change anything else. However, if this isn't your use case
(converting a pyevent application), you can pretty much ignore this and use
rel directly.

Anyway, dez is full of rel example code. One concise example is the SocketDaemon
in the [server submodule](https://github.com/bubbleboy14/dez/blob/master/dez/network/server.py) of [dez.network](https://github.com/bubbleboy14/dez/tree/master/dez/network):

    class SocketDaemon(object):
        def __init__(self, hostname, port, cb=None, b64=False, cbargs=[], certfile=None, keyfile=None, cacerts=None):
            self.log = default_get_logger("SocketDaemon")
            self.hostname = hostname
            self.port = port
            self.sock = io.server_socket(self.port, certfile, keyfile, cacerts)
            self.cb = cb
            self.cbargs = cbargs
            self.b64 = b64
            self.secure = bool(certfile)
            self.listen = event.read(self.sock, self.accept_connection)

        def handshake_cb(self, sock, addr):
            def cb():
                conn = Connection(addr, sock, b64=self.b64)
                if self.cb:
                    self.cb(conn, *self.cbargs)
            return cb

        def accept_connection(self):
            try:
                sock, addr = self.sock.accept()
                cb = self.handshake_cb(sock, addr)
                if self.secure:
                    io.ssl_handshake(sock, cb)
                    return True
            except io.socket.error as e:
                self.log.info("abandoning connection on socket error: %s"%(e,))
                return True
            cb()
            return True

        def start(self):
            event.signal(2, event.abort)
            event.dispatch()

Another short example, also in [dez.network](https://github.com/bubbleboy14/dez/tree/master/dez/network), is to be found in the [controller submodule](https://github.com/bubbleboy14/dez/blob/master/dez/network/controller.py):

    class SocketController(object):
        def __init__(self):
            self.daemons = {}

        def register_address(self, hostname, port, callback=None, cbargs=[], b64=False, daemon="socket", dclass=None):
            d = self.daemons.get((hostname, port))
            if d:
                d.cb = callback
                d.cbargs = cbargs
            else:
                dclass = dclass and daemon_wrapper(dclass) or heads[daemon]
                d = dclass(hostname, port, callback, b64, cbargs=cbargs)
                self.daemons[(hostname, port)] = d
            return d

        def _abort(self):
            if self.onstop:
                self.onstop()
            event.abort()

        def start(self, onstop=False):
            if not self.daemons:
                print("SocketController doesn't know where to listen. Use register_address(hostname, port, callback) to register server addresses.")
                return
            self.onstop = onstop
            event.signal(2, self._abort)
            event.dispatch()

Other brief examples are sprinkled throughout [dez.http](https://github.com/bubbleboy14/dez/tree/master/dez/http), including in [HTTPApplication](https://github.com/bubbleboy14/dez/blob/master/dez/http/application.py), [Shield](https://github.com/bubbleboy14/dez/blob/master/dez/http/server/shield.py), [fetch](https://github.com/bubbleboy14/dez/blob/master/dez/http/fetch.py), [inotify](https://github.com/bubbleboy14/dez/blob/master/dez/http/inotify.py), and elsewhere.

## registrar.py

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

## test.py

REL Test Suite - regular unittest compatible suite
Submitted by Chris Clark on 10/12/2011. Thanks, Chris!

Original code here:
http://code.google.com/r/clach04-pyeventtestfixes/source/browse/test.py

Sample usage:

    rel\test.py
    rel\test.py -v
    rel\test.py -v EventTest.test_exception EventTest.test_timeout
    ... etc.

## tools.py

This module contains a single tool (Timer) and a
CLI wrapper (timerCLI()).

### Timer
Timer's start() function contains basic usage examples
of the timeout(), signal(), and dispatch() functions:

    def start(self):
        self.count = 0
        notice("starting countdown to %s"%(self.goal,))
        rel.timeout(1, self.update)
        rel.signal(2, self.stop)
        rel.dispatch()

Similarly, Timer.stop() triggers rel.abort().

### timerCLI
This function contains an example of rel initialization,
which is optional, but may be used to specify particular
settings:

    if options.verbose:
        rel.initialize(options=["verbose"])

### usage

    rtimer [seconds] [minutes] [hours] [update_increment]

All arguments default to zero. So:

    rtimer 15 30 2 60

means run for 15 seconds, 30 minutes, and 2 hours, printing
a notice every 60 seconds.

    rtimer 0 5

means run for 5 minutes, printing no incremental updates.

When the time runs out, a sound will play on two conditions:
there is a readable file at the specified path (configurable
via the -m flag, with default: /var/local/rtimer_elapsed.mp3),
and mplayer is installed.

## listener.py

This module includes four classes: Event, SocketIO, Signal, and Timer.

### Event
This class uses a Registrar subclass instance to manage read, write,
signal, and timeout events.

### SocketIO
This class uses a Registrar subclass instance to manage read, and
write events.

### Signal
This class uses the signal library and a Registrar subclass instance
to manage signal events.

### Timer
This class uses a Registrar subclass to manage timer events.

## rel.py

R.E.L.
Registed Event Listener is a pure-python implementation of [pyevent](https://github.com/jaraco/pyevent),
which is a wrapper around [libevent](http://monkey.org/~provos/libevent/), providing an identical interface
without the need to compile C code, and without breaking the GIL / threading.

### basic functions:
    read(socket, callback, *args)
    write(socket, callback, *args)
    timeout(delay, callback, *args)
    signal(sig, callback, *args)
    event(callback,arg=None,evtype=0,handle=None)
    dispatch()
    loop()
    abort()
    abort_branch() (non-pyevent only)
    thread()
    init()

### registrars
rel will use the fastest registrar available on your system:

    supported_methods = ['epoll','poll','kqueue','select','pyevent']

The supported_methods[] registrar priority list, as well as other
settings, can be altered using the (optional) initialize() function:

### initialize(methods=supported_methods,options=()) - possible options:
    'verbose' - prints out certain events
    'report' - prints status of non-pyevent registrar every 5 seconds
    'strict' - ONLY try specified methods
    'threaded' - enable GIL hack -- pyevent only!

### override()
This override function can be used to seamlessly swap rel into
a pyevent application.