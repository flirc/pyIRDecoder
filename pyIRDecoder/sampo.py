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


TIMING = 833


class Sampo(protocol_base.IrProtocolBase):
    """
    IR decoder for the Sampo protocol.
    """
    irp = '{38.4k,833,lsb}<1,-1|1,-3>(4,-4,D:6,F:6,S:6,~F:6,1,-39)*'
    frequency = 38400
    bit_count = 24
    encoding = 'lsb'

    _lead_in = [TIMING * 4, -TIMING * 4]
    _lead_out = [TIMING, -TIMING * 39]
    _middle_timings = []
    _bursts = [[TIMING, -TIMING], [TIMING, -TIMING * 3]]

    _repeat_lead_in = []
    _repeat_lead_out = []
    _repeat_bursts = []

    _parameters = [
        ['D', 0, 5],
        ['F', 6, 11],
        ['S', 12, 17],
        ['F_CHECKSUM', 18, 23]
    ]
    # [D:0..63,S:0..63,F:0..63]
    encode_parameters = [
        ['device', 0, 63],
        ['sub_device', 0, 63],
        ['function', 0, 63],
    ]

    def _calc_checksum(self, function):
        f = self._invert_bits(function, 6)
        return f

    def decode(self, data, frequency=0):
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)

        if self._last_code is not None:
            if self._last_code == code:
                return self._last_code

            self._last_code.repeat_timer.stop()
            self._last_code = None

        func_checksum = self._calc_checksum(code.function)

        if func_checksum != code.f_checksum:
            raise DecodeError('Checksum failed')

        self._last_code = code
        return code

    def encode(self, device, sub_device, function, repeat_count=0):
        func_checksum = self._calc_checksum(function)

        packet = self._build_packet(
            list(self._get_timing(device, i) for i in range(6)),
            list(self._get_timing(function, i) for i in range(6)),
            list(self._get_timing(sub_device, i) for i in range(6)),
            list(self._get_timing(func_checksum, i) for i in range(6))
        )

        return [packet] * (repeat_count + 1)

    def _test_decode(self):
        rlc = [[
            3332, -3332, 833, -2499, 833, -833, 833, -2499, 833, -2499, 833, -2499, 833, -2499, 
            833, -2499, 833, -2499, 833, -2499, 833, -833, 833, -2499, 833, -833, 833, -833, 
            833, -833, 833, -833, 833, -833, 833, -2499, 833, -833, 833, -833, 833, -833, 
            833, -833, 833, -2499, 833, -833, 833, -2499, 833, -32487, 
        ]]

        params = [dict(device=61, function=23, sub_device=16)]

        return protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        params = dict(device=61, function=23, sub_device=16)
        protocol_base.IrProtocolBase._test_encode(self, params)


Sampo = Sampo()
