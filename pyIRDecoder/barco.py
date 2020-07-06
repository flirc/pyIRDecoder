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


TIMING = 10


class Barco(protocol_base.IrProtocolBase):
    """
    IR decoder for the Barco protocol.
    """
    irp = '{0k,10,lsb}<1,-5|1,-15>(1,-25,D:5,F:6,1,-25,1,120m)+ '
    frequency = 0
    bit_count = 11
    encoding = 'lsb'

    _lead_in = [TIMING, -TIMING * 25]
    _lead_out = [TIMING, -TIMING * 25, TIMING, -120000]
    _middle_timings = []
    _bursts = [[TIMING, -TIMING * 5], [TIMING, -TIMING * 15]]

    _repeat_lead_in = []
    _repeat_lead_out = []
    _repeat_bursts = []

    _parameters = [
        ['D', 0, 4],
        ['F', 5, 10],
    ]
    # [D:0..31,F:0..63]
    encode_parameters = [
        ['device', 0, 31],
        ['function', 0, 63],
    ]

    def encode(self, device, function, ):
        packet = self._build_packet(
            list(self._get_timing(device, i) for i in range(5)),
            list(self._get_timing(function, i) for i in range(6)),
        )

        return [packet]

    def _test_decode(self):
        rlc = [[
            10, -250, 10, -50, 10, -50, 10, -50, 10, -50, 10, -150, 10, -50, 10, -50, 10, -150, 10, -150, 10, -50,
            10, -150, 10, -250, 10, -120000
        ]]

        params = [dict(device=16, function=44)]

        return protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        params = dict(device=16, function=44)
        protocol_base.IrProtocolBase._test_encode(self, params)


Barco = Barco()

