More and more applications are coming to rely on pyevent. The problem is that pyevent itself requires compiling external modules and therefore presents a deployment hurdle. The rel module is a drop-in replacement for pyevent that completely emulates pyevent's interface, behavior and functionality on any system with Python. It will use pyevent if it's available, and if it's not rel will use the fastest method supported by the system. Epoll, poll, kqueue, and select are currently implemented.

To use rel:
  1. download it: 'sudo easy\_install rel' or install the package hosted here.
  1. put 'import rel; rel.override()' at the top of the start script for your prevent application