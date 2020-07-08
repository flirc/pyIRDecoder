# -*- coding: utf-8 -*-
#
# ***********************************************************************************
# MIT License
#
# Copyright (c) 2020 Kevin G. Schlosser
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# ***********************************************************************************

# Local imports
from . import protocol_base
from . import DecodeError


TIMING = 630


class PaceMSS(protocol_base.IrProtocolBase):
    """
    IR decoder for the PaceMSS protocol.
    """
    irp = '{38k,630,msb}<1,-7|1,-11>(1,-5,1,-5,T:1,D:1,F:8,1,^120m)*'
    frequency = 38000
    bit_count = 10
    encoding = 'msb'

    _lead_in = [TIMING, -TIMING * 5, TIMING, -TIMING * 5]
    _lead_out = [TIMING, 120000]
    _bursts = [[TIMING, -TIMING * 7], [TIMING, -TIMING * 11]]

    _current_toggle = 0

    _parameters = [
        ['T', 0, 0],
        ['D', 1, 1],
        ['F', 2, 9],
    ]
    # [D:0..1,F:0..255,T:0..1]
    encode_parameters = [
        ['device', 0, 1],
        ['function', 0, 255],
    ]

    def decode(self, data, frequency=0):
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)

        if self._last_code is not None:
            if (
                self._last_code == code and
                self._last_code.toggle == code.toggle
            ):
                return self._last_code

            self._last_code.repeat_timer.stop()

        self._last_code = code
        return code

    def encode(self, device, function, repeat_count=0):
        self._current_toggle = int(not self._current_toggle)

        packet = self._build_packet(
            list(self._get_timing(self._current_toggle, i) for i in range(1)),
            list(self._get_timing(device, i) for i in range(1)),
            list(self._get_timing(function, i) for i in range(8))
        )

        return [packet] * (repeat_count + 1)

    def _test_decode(self):
        rlc = [[
            630, -3150, 630, -3150, 630, -4410, 630, -4410, 630, -6930, 630, -4410, 630, -4410,
            630, -6930, 630, -6930, 630, -4410, 630, -4410, 630, -4410, 630, -53850,
        ]]

        params = [dict(function=152, toggle=0, device=0)]
        return protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        params = dict(function=152, toggle=0, device=0)
        protocol_base.IrProtocolBase._test_encode(self, params)


PaceMSS = PaceMSS()
