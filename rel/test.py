"""
REL Test Suite - regular unittest compatible suite
Submitted by Chris Clark on 10/12/2011. Thanks, Chris!

Original code here:
http://code.google.com/r/clach04-pyeventtestfixes/source/browse/test.py

Sample usage:

    rel\test.py
    rel\test.py -v
    rel\test.py -v EventTest.test_exception EventTest.test_timeout
    ... etc.
"""

from . import rel
rel.override()

import glob
import os
import signal
import sys
import _thread
import time
import unittest

"""
# skip code, disabled due to odd raise in Cython code
try:
    if sys.version_info < (2, 3):
        # unittest2 needs 2.3+
        raise ImportError
    import unittest2
    unittest = unittest2
except ImportError:
    import unittest
    unittest2 = None
"""
unittest2 = None

# Note "setup.py develop" is preferred mechanism for build areas
possible_build_dir = glob.glob('./build/lib.*')
if possible_build_dir:
    sys.path.insert(0, possible_build_dir[0])

import event

class EventTest(unittest.TestCase):

    def skip(self, reason):
        """Skip current test because of `reason`.
       
        NOTE currently expects unittest2, and defaults to "pass"
        if not available.
       
        unittest2 does NOT work under Python 2.2.
        Could potentially use nose or py.test which has (previously)
        supported Python 2.2
          * nose
            http://python-nose.googlecode.com/svn/wiki/NoseWithPython2_2.wiki
          * py.test
            http://codespeak.net/pipermail/py-dev/2005-February/000203.html
        """
        if unittest2:
            raise unittest2.SkipTest(reason)

    def setUp(self):
        self.call_back_ran = False
        event.init()

    def test_timeout(self):
        def __timeout_cb(ev, handle, evtype, ts):
            now = time.time()
            self.call_back_ran = True
            assert int(now - ts['start']) == ts['secs'], 'timeout failed'
        ts = {'start': time.time(), 'secs': 5}
        ev = event.event(__timeout_cb, arg=ts)
        ev.add(ts['secs'])
        event.dispatch()
        self.assertTrue(self.call_back_ran, 'call back did not run')

    def test_timeout2(self):
        def __timeout2_cb(start, secs):
            self.call_back_ran = True
            dur = int(time.time() - start)
            assert dur == secs, 'timeout2 failed'
        event.timeout(5, __timeout2_cb, time.time(), 5)
        event.dispatch()
        self.assertTrue(self.call_back_ran, 'call back did not run')
   
    def test_signal(self):
        if not hasattr(signal, 'SIGUSR1'):
            self.skip('signal.SIGUSR1 missing (probably Windows)')
        else:
           
            def __signal_cb(ev, sig, evtype, arg):
                if evtype == event.EV_SIGNAL:
                    ev.delete()
                elif evtype == event.EV_TIMEOUT:
                    os.kill(os.getpid(), signal.SIGUSR1)
            event.event(__signal_cb, handle=signal.SIGUSR1,
                        evtype=event.EV_SIGNAL).add()
            event.event(__signal_cb).add(2)
            event.dispatch()

    def test_signal2(self):
        if not hasattr(signal, 'SIGUSR1'):
            self.skip('signal.SIGUSR1 missing (probably Windows)')
        else:
           
            def __signal2_cb(sig):
                if sig:
                    event.abort()
                else:
                    os.kill(os.getpid(), signal.SIGUSR1)
            event.signal(signal.SIGUSR1, __signal2_cb, signal.SIGUSR1)
            event.timeout(2, __signal2_cb)

    def test_read(self):
        def __read_cb(ev, fd, evtype, pipe):
            self.call_back_ran = True
            buf = os.read(fd, 1024)
            assert buf == b'hi niels', 'read event failed'
        pipe = os.pipe()
        event.event(__read_cb, handle=pipe[0],
                    evtype=event.EV_READ).add()
        os.write(pipe[1], b'hi niels')
        event.dispatch()
        self.assertTrue(self.call_back_ran, 'call back did not run')

    def test_read2(self):
        def __read2_cb(fd, msg):
            self.call_back_ran = True
            assert os.read(fd, 1024) == msg, 'read2 event failed'
        msg = b'hello world'
        pipe = os.pipe()
        event.read(pipe[0], __read2_cb, pipe[0], msg)
        os.write(pipe[1], msg)
        event.dispatch()
        self.assertTrue(self.call_back_ran, 'call back did not run')

    def test_exception(self):
        def __bad_cb(foo):
            raise NotImplementedError(foo)

        def real_test_exception():
            event.timeout(0, __bad_cb, 'bad callback')
            event.dispatch()

        self.assertRaises(NotImplementedError, real_test_exception)

    def test_abort(self):
        def __time_cb():
            raise NotImplementedError('abort failed!')
        event.timeout(5, __time_cb)
        event.timeout(1, event.abort)
        event.dispatch()

    def test_callback_exception(self):
        def __raise_cb(exc):
            raise exc

        def __raise_catch_cb(exc):
            try:
                raise exc
            except:
                pass
        event.timeout(0, __raise_cb, Exception())
        event.timeout(0, __raise_catch_cb, Exception())
        self.assertRaises(Exception, event.dispatch)

    def test_thread(self):
        self.call_back_ran_a = False
        self.call_back_ran_b = False

        def __time_cb(d):
            self.call_back_ran_a = True
            assert d['count'] == 3

        def __time_thread(count, d):
            self.call_back_ran_b = True
            for i in range(count):
                time.sleep(1)
                d['count'] += 1
        d = {'count': 0}
        _thread.start_new_thread(__time_thread, (3, d))
        event.timeout(4, __time_cb, d)
        event.dispatch()
        self.assertTrue(self.call_back_ran_a, 'call back a did not run')
        self.assertTrue(self.call_back_ran_b, 'call back b did not run')

if __name__ == '__main__':
    if input("run these tests with select registrar? (y/N)").lower().startswith("y"):
        rel.initialize(['select'], ['verbose', 'strict'])
    elif input('verbose mode? (y/N)').lower().startswith('y'):
        rel.initialize(options=['verbose'])
    unittest.main()
