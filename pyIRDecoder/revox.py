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


TIMING = 15


class Revox(protocol_base.IrProtocolBase):
    """
    IR decoder for the Revox protocol.
    """
    irp = '{0k,15,lsb}<1,-9|1,-19>(1,-29,0:1,D:4,F:6,1,-29,1,-100285u)*'
    frequency = 0
    bit_count = 11
    encoding = 'lsb'

    _lead_in = [TIMING, -TIMING * 29]
    _lead_out = [TIMING, -TIMING * 29, TIMING, -100285]
    _middle_timings = []
    _bursts = [[TIMING, -TIMING * 9], [TIMING, -TIMING * 19]]

    _repeat_lead_in = []
    _repeat_lead_out = []
    _repeat_bursts = []

    _parameters = [
        ['C0', 0, 0],
        ['D', 1, 4],
        ['F', 5, 10]
    ]
    # [D:0..15,F:0..63]
    encode_parameters = [
        ['device', 0, 15],
        ['function', 0, 63],
    ]

    def decode(self, data, frequency=0):
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)

        if code.c0 != 0:
            raise DecodeError('Checksum failed')

        return code

    def encode(self, device, function):
        c0 = 0

        packet = self._build_packet(
            list(self._get_timing(c0, i) for i in range(1)),
            list(self._get_timing(device, i) for i in range(4)),
            list(self._get_timing(function, i) for i in range(6))
        )

        return [packet]

    def _test_decode(self):
        rlc = [[
            15, -435, 15, -135, 15, -285, 15, -285, 15, -135, 15, -285, 15, -285, 15, -135, 
            15, -135, 15, -135, 15, -285, 15, -135, 15, -435, 15, -100285, 
        ]]

        params = [dict(device=11, function=17)]

        protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        params = dict(device=11, function=17)
        protocol_base.IrProtocolBase._test_encode(self, params)


Revox = Revox()
