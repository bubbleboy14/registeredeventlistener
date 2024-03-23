"""
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

The -s, -m, -r, and -i flags may also be used to indicate
seconds, minutes, hours, and increment, and if any flag is
specified, update_increment defaults to 1 (instead of 0).

When the time runs out, a sound will play on two conditions:
there is a readable file at the specified path (configurable
via the -p flag, with default: ~/.rtimer/),
and mplayer is installed.
"""

import rel, os, random
try:
    from subprocess import getoutput # py3
except:
    from commands import getoutput # py2

### helper functions

def notice(*lines):
    print("")
    print("\n".join(lines))

def exit():
    notice("goodbye")
    if rel.is_running():
        rel.abort()
    else:
        import sys
        sys.exit()

def error(msg, *lines):
    notice("fatal exception!", "error: %s"%(msg,), *lines)
    exit()

### the tools themselves

# rtimer

RT_MEDIA = os.path.join(os.path.expanduser("~"), ".rtimer")
RT_USAGE = 'rtimer [seconds] [minutes] [hours] [update_increment]\n--\nall arguments default to zero. so, rtimer 15 30 2 60 means run for 15 seconds, 30 minutes, and 2 hours, printing a notice every 60 seconds. rtimer 0 5 means run for 5 minutes, printing no incremental updates. the -s, -m, -r, and -i flags may also be used to indicate seconds, minutes, hours, and increment, and if any flag is specified, update_increment defaults to 1 (instead of 0). when the time runs out, a sound will play on two conditions: there is a readable file at the specified path (default: %s), and mplayer is installed.'%(RT_MEDIA,)

class Timer(object):
    def __init__(self, s, m, h, interval=0, mediapath=RT_MEDIA):
        try:
            s, m, h, self.interval = int(s), int(m), int(h), int(interval)
        except:
            error("invalid input", "seconds, minutes, hours, and interval must all be integers")
        self.count = 0
        self.goal = s + m * 60 + h * 3600
        if self.count == self.goal:
            notice("USAGE: %s"%(RT_USAGE,))
            exit()
        self.media = mediapath
        problem = "no sound file path specified"
        if self.media:
            if "command not found" in getoutput("mplayer"):
                self.media = None
                problem = "could not find mplayer!"
            elif not os.path.isdir(self.media):
                self.media = None
                problem = "media directory not found! please mkdir ~/.rtimer/ and add some media files!"
        self.media or notice("media notification disabled", problem)

    def start(self):
        self.count = 0
        notice("starting countdown to %s"%(self.goal,))
        rel.timeout(1, self.update)
        rel.signal(2, self.stop)
        rel.dispatch()

    def stop(self):
        notice("stopping timer at %s"%(self.count,))
        exit()

    def update(self):
        self.count += 1
        if self.interval and not self.count % self.interval:
            s = self.count % 60
            if s < 10:
                s = "0%s"%(s,)
            tstamp = "%s:%s"%(int(self.count / 60), s)
            notice("count: %s. goal: %s. time: %s. completed: %s%%."%(self.count,
                self.goal, tstamp, str(100 * self.count/float(self.goal))[:5]))
        if self.count == self.goal:
            self.alarm()
        return True

    def alarm(self):
        notice("time's up!")
        if self.media:
            getoutput("mplayer %s"%(os.path.join(self.media, random.choice(os.listdir(self.media))),))
        self.stop()

### functions for interpreting command-line instructions

# rtimer

def timerCLI():
    from optparse import OptionParser
    parser = OptionParser(RT_USAGE)
    parser.add_option("-r", "--hours", dest="hours", default=0, help="hours. default: 0")
    parser.add_option("-m", "--minutes", dest="minutes", default=0, help="minutes. default: 0")
    parser.add_option("-s", "--seconds", dest="seconds", default=0, help="seconds. default: 0")
    parser.add_option("-i", "--increment", dest="increment", default=1, help="increment. default: 1")
    parser.add_option("-p", "--path", dest="path", default=RT_MEDIA, help="location of alarm media (audio/video) directory. default: %s"%(RT_MEDIA,))
    parser.add_option("-v", "--verbose", dest="verbose", default=False, action="store_true", help="run timer in verbose mode")
    options, arguments = parser.parse_args()
    if options.verbose:
        rel.initialize(options=["verbose"])
    try:
        arguments = [int(arg) for arg in arguments]
    except:
        error("non-integer argument", "USAGE: %s"%(RT_USAGE,))
    while len(arguments) < 4:
        arguments.append(0)
    if options.seconds or options.minutes or options.hours or options.increment:
        arguments[0] = arguments[0] or int(options.seconds)
        arguments[1] = arguments[1] or int(options.minutes)
        arguments[2] = arguments[2] or int(options.hours)
        arguments[3] = arguments[3] or int(options.increment)
    arguments.append(options.path)
    Timer(*arguments).start()
