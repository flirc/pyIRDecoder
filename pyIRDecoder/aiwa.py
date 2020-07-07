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

TIMING = 550


class Aiwa(protocol_base.IrProtocolBase):
    """
    IR decoder for the Aiwa protocol.
    """
    irp = '{38.123k,550,lsb}<1,-1|1,-3>(16,-8,D:8,S:5,~D:8,~S:5,F:8,~F:8,1,-42,(16,-8,1,-165)*)'
    frequency = 38123
    bit_count = 42
    encoding = 'lsb'

    _lead_in = [TIMING * 16, -TIMING * 8]
    _lead_out = [TIMING, -TIMING * 42]
    _bursts = [[TIMING, -TIMING], [TIMING, -TIMING * 3]]

    _repeat_lead_in = [TIMING * 16, -TIMING * 8]
    _repeat_lead_out = [TIMING, -TIMING * 165]

    _parameters = [
        ['D', 0, 7],
        ['S', 8, 12],
        ['D_CHECKSUM', 13, 20],
        ['S_CHECKSUM', 21, 25],
        ['F', 26, 33],
        ['F_CHECKSUM', 34, 41],
    ]
    # [D:0..255,S:0..31,F:0..255]
    encode_parameters = [
        ['device', 0, 255],
        ['sub_device', 0, 31],
        ['function', 0, 255],
    ]

    def _calc_checksum(self, device, sub_device, function):
        d = self._invert_bits(device, 8)
        s = self._invert_bits(sub_device, 5)
        f = self._invert_bits(function, 8)

        return d, s, f

    def decode(self, data, frequency=0):
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)
        if self._last_code is not None and self._last_code == code:
            return code

        device_checksum, sub_checksum, func_checksum = (
            self._calc_checksum(code.device, code.sub_device, code.function)
        )

        if (
            device_checksum != code.d_checksum or
            sub_checksum != code.s_checksum or
            func_checksum != code.f_checksum
        ):
            self._last_code = None
            raise DecodeError('Checksum failed')

        return code

    def encode(self, device, sub_device, function, repeat_count=0):
        dev_checksum, sub_checksum, func_checksum = (
            self._calc_checksum(device, sub_device, function)
        )

        packet = [
            self._build_packet(
                list(self._get_timing(device, i) for i in range(8)),
                list(self._get_timing(sub_device, i) for i in range(5)),
                list(self._get_timing(dev_checksum, i) for i in range(8)),
                list(self._get_timing(sub_checksum, i) for i in range(5)),
                list(self._get_timing(function, i) for i in range(8)),
                list(self._get_timing(func_checksum, i) for i in range(8))
            )
        ]
        packet += self._build_repeat_packet(repeat_count)
        return packet

    def _test_decode(self):
        rlc = [
            [
                +8800, -4400, +550, -550, +550, -1650, +550, -550, +550, -550, +550, -550, +550, -1650, +550, -550,
                +550, -550, +550, -1650, +550, -550, +550, -550, +550, -550, +550, -1650, +550, -1650, +550, -550,
                +550, -1650, +550, -1650, +550, -1650, +550, -550, +550, -1650, +550, -1650, +550, -550, +550, -1650,
                +550, -1650, +550, -1650, +550, -550, +550, -550, +550, -1650, +550, -1650, +550, -1650, +550, -550,
                +550, -550, +550, -550, +550, -550, +550, -1650, +550, -550, +550, -550, +550, -550, +550, -1650,
                +550, -1650, +550, -1650, +550, -1650, +550, -23100
            ],
            # [+8800, -4400, +550, -90750]
        ]

        params = [dict(device=34, function=14, sub_device=17)]  # dict(device=34, function=14, sub_device=17)]

        return protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        params = dict(device=34, function=14, sub_device=17)
        protocol_base.IrProtocolBase._test_encode(self, params)


Aiwa = Aiwa()
