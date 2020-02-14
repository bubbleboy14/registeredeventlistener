### rel tools module.
### (mostly rel example code)

import rel
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
    if rel.running:
        rel.abort()
    else:
        import sys
        sys.exit()

def error(msg, *lines):
    notice("fatal exception!", "error: %s"%(msg,), *lines)
    exit()

### the tools themselves

# rtimer

RT_MP3 = '/var/local/rtimer_elapsed.mp3'
RT_USAGE = 'rtimer [seconds] [minutes] [hours] [update_increment]\n--\nall arguments default to zero. so, rtimer 15 30 2 60 means run for 15 seconds, 30 minutes, and 2 hours, printing a notice every 60 seconds. rtimer 0 5 means run for 5 minutes, printing no incremental updates. when the time runs out, a sound will play on two conditions: there is a readable file at the specified path (default: %s), and mplayer is installed.'%(RT_MP3,)

class Timer(object):
    def __init__(self, s, m, h, interval=0, mp3=RT_MP3):
        try:
            s, m, h, self.interval = int(s), int(m), int(h), int(interval)
        except:
            error("invalid input", "seconds, minutes, hours, and interval must all be integers")
        self.count = 0
        self.goal = s + m * 60 + h * 360
        if self.count == self.goal:
            notice("USAGE: %s"%(RT_USAGE,))
            exit()
        self.mp3 = mp3
        problem = "no sound file path specified"
        if self.mp3:
            import os
            if "command not found" in getoutput("mplayer"):
                self.mp3 = None
                problem = "could not find mplayer!"
            elif not os.path.isfile(mp3):
                self.mp3 = None
                problem = "could not access sound file at %s -- no such file"%(mp3,)
            else:
                try:
                    f = open(mp3)
                    f.close()
                except:
                    self.mp3 = None
                    problem = "could not access sound file at %s -- permission denied"%(mp3,)
        if not self.mp3:
            notice("sound disabled", problem)

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
            notice("count: %s. goal: %s. completed: %s%%."%(self.count, self.goal, str(self.count/float(self.goal))[:5]))
        if self.count == self.goal:
            self.alarm()
        return True

    def alarm(self):
        notice("time's up!")
        if self.mp3:
            getoutput("mplayer %s"%(self.mp3,))
        self.stop()

### functions for interpreting command-line instructions

# rtimer

def timerCLI():
    from optparse import OptionParser
    parser = OptionParser(RT_USAGE)
    parser.add_option("-m", "--mp3_file_path", dest="mp3", default=RT_MP3, help="location of alarm sound mp3. default: %s"%(RT_MP3,))
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
    arguments.append(options.mp3)
    Timer(*arguments).start()
