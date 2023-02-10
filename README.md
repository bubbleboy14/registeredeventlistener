More and more applications are coming to rely on pyevent. The problem is that pyevent itself requires compiling external modules and therefore presents a deployment hurdle. The rel module is a drop-in replacement for pyevent that completely emulates pyevent's interface, behavior and functionality on any system with Python. It will use pyevent if preferred/available, and otherwise rel will use the fastest method supported by the system. Epoll, poll, kqueue, and select are currently implemented.

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