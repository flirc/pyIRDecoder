# -*- coding: utf-8 -*-
#
# *****************************************************************************
# MIT License
#
# Copyright (c) 2020 Kevin G. Schlosser
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.

# ****************************************************************************

import ctypes
import sys
import threading


if sys.platform.startswith('win'):
    LARGE_INTEGER = ctypes.c_int64
    BOOL = ctypes.c_bool

    _kernel32 = ctypes.windll.Kernel32

    # BOOL QueryPerformanceCounter(
    #   LARGE_INTEGER *lpPerformanceCount
    # );
    _QueryPerformanceCounter_ = _kernel32.QueryPerformanceCounter
    _QueryPerformanceCounter_.argtypes = [ctypes.POINTER(LARGE_INTEGER)]
    _QueryPerformanceCounter_.restype = BOOL

    # BOOL QueryPerformanceFrequency(
    #   LARGE_INTEGER *lpFrequency
    # );
    _QueryPerformanceFrequency_ = _kernel32.QueryPerformanceFrequency
    _QueryPerformanceFrequency_.argtypes = [ctypes.POINTER(LARGE_INTEGER)]
    _QueryPerformanceFrequency_.restype = BOOL

    def _get_counter():

        lpPerformanceCount = LARGE_INTEGER()
        lpFrequency = LARGE_INTEGER()

        if (
            not _QueryPerformanceCounter_(ctypes.byref(lpPerformanceCount)) or
            not _QueryPerformanceFrequency_(ctypes.byref(lpFrequency))
        ):
            raise ctypes.WinError()

        return lpPerformanceCount.value, lpFrequency.value


    def micros():
        """
        microseconds (us)
        """
        count, freq = _get_counter()
        return count * 1e6 / freq

    def millis():
        """
        milliseconds (ms)
        """
        count, freq = _get_counter()
        return count * 1e3 / freq

else:
    import os

    CLOCK_MONOTONIC_RAW = 4

    class timespec(ctypes.Structure):
        _fields_ = [
            ('tv_sec', ctypes.c_long),
            ('tv_nsec', ctypes.c_long)
        ]

    librt = ctypes.CDLL('librt.so.1', use_errno=True)
    clock_gettime = librt.clock_gettime
    clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(timespec)]

    def monotonic_time():
        """
        seconds (sec)
        """
        t_spec = timespec()

        if clock_gettime(CLOCK_MONOTONIC_RAW, ctypes.pointer(t_spec)) != 0:
            errno_ = ctypes.get_errno()
            raise OSError(errno_, os.strerror(errno_))

        return t_spec.tv_sec + t_spec.tv_nsec * 1e-9

    def micros():
        """
        microseconds (us)
        """
        return monotonic_time() * 1e6

    def millis():
        """
        milliseconds (ms)
        """
        return monotonic_time() * 1e3


def wait_milliseconds(duration):
    """
    millisecond blocking delay (minimum spinning wheel)
    """
    t_start = millis()

    event = threading.Event()
    event_wait = (float(duration - (millis() - t_start)) * 0.90)
    if event_wait >= 10:
        event.wait(event_wait / 1000.0)
    while millis() - t_start < duration:
        pass

    return


def wait_microseconds(duration):
    """
    microseconds blocking delay (minimum spinning wheel)
    """
    t_start = micros()
    event = threading.Event()
    event_wait = float(duration - (micros() - t_start)) * 0.80

    if event_wait >= 10000:
        event.wait(event_wait / 1000000.0)

    while micros() - t_start < duration:
        pass

    return


class TimerUS(object):
    def __init__(self):
        self.start = 0
        self.event = threading.Event()
        self.reset()

    def reset(self):
        self.start = micros()

    def elapsed(self):
        now = micros()
        return now - self.start

    def set(self):
        self.event.set()

    def is_set(self):
        return self.event.is_set()

    def clear(self):
        self.event.clear()

    def wait(self, duration):
        """
        blocking delay (minimum spinning wheels)
        """

        # I wanted to create a blocking wait/delay that didn't cause a
        # "spinning wheel" (high cpu use). Using an event does this but the
        # problem with it is it's not consistant. It will release the wait
        # before the timeout period or after the timeout period. If it was one
        # or the other I could compensate for it somewhat. So what I did is I
        # am using the threading.Event.wait for a portion of the duration.
        # leaving about a 2.5% buffer. I found that threading.Event.wait
        # releases < +- 2.5%. At that point I then do a spinning wheel. When
        # wanting for wait for microseconds or milliseconds this works really
        # well and manages to keep the load on the CPU low. and when it
        # releases it is typiclly around 3-4 microseconds past the wanted time.
        # Which isn't bad at all. Much better then the 4-5 milliseconds from
        # threading.Event.wait
        event = threading.Event()
        event_wait = float(duration - (micros() - self.start)) * 0.80

        if event_wait >= 10000:
            event.wait(event_wait / 1000000.0)

        while not self.is_set() and micros() - self.start < duration:
            pass


class TimerMS(object):
    def __init__(self):
        self.start = 0
        self.event = threading.Event()
        self.reset()

    def reset(self):
        self.start = millis()

    def elapsed(self):
        now = millis()
        return now - self.start

    def set(self):
        self.event.set()

    def is_set(self):
        return self.event.is_set()

    def clear(self):
        self.event.clear()

    def wait(self, duration):
        """
        blocking delay (minimum spinning wheels)
        """
        event_wait = (float(duration - (millis() - self.start)) * 0.90)
        if event_wait >= 10:
            self.event.wait(event_wait / 1000.0)

        while not self.is_set() and millis() - self.start < duration:
            pass


if __name__ == '__main__':
    t = TimerMS()
    t.wait(50)
    print(t.elapsed())
