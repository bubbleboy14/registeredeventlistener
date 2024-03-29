from _typeshed import Incomplete

EV_PERSIST: int
EV_READ: int
EV_SIGNAL: int
EV_TIMEOUT: int
EV_WRITE: int
noadd: str

def contains(mode, bit): ...

class Event:
    registrar: Incomplete
    cb: Incomplete
    arg: Incomplete
    timeout: Incomplete
    evtype: Incomplete
    handle: Incomplete
    children: Incomplete
    def __init__(self, registrar, cb, arg, evtype, handle) -> None: ...
    def spawn_children(self) -> None: ...
    def add(self, delay: Incomplete | None = ...) -> None: ...
    def delete(self) -> None: ...
    def pending(self): ...
    def callback(self) -> None: ...

class SocketIO:
    registrar: Incomplete
    evtype: Incomplete
    sock: Incomplete
    fd: Incomplete
    cb: Incomplete
    args: Incomplete
    persist: bool
    active: int
    timeout: Incomplete
    def __init__(self, registrar, evtype, sock, cb, *args) -> None: ...
    def persistent(self) -> None: ...
    def add(self, delay: Incomplete | None = ...) -> None: ...
    def delete(self) -> None: ...
    def dereference(self) -> None: ...
    def pending(self): ...
    def callback(self) -> None: ...

class Signal:
    registrar: Incomplete
    sig: Incomplete
    default: Incomplete
    cb: Incomplete
    args: Incomplete
    timeout: Incomplete
    def __init__(self, registrar, sig, cb, *args) -> None: ...
    active: int
    def add(self, delay: Incomplete | None = ...) -> None: ...
    def delete(self) -> None: ...
    def reset(self) -> None: ...
    def pending(self): ...
    def callback(self, *args) -> None: ...

class Timer:
    registrar: Incomplete
    cb: Incomplete
    args: Incomplete
    def __init__(self, registrar, delay, cb, *args) -> None: ...
    delay: Incomplete
    expiration: Incomplete
    def add(self, delay: Incomplete | None = ...) -> None: ...
    def delete(self, dereference: bool = ...) -> None: ...
    def pending(self): ...
    def check(self, t: Incomplete | None = ...): ...
