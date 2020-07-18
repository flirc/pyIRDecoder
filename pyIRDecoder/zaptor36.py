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
from . import DecodeError, RepeatLeadOut

TIMING = 330


class Zaptor36(protocol_base.IrProtocolBase):
    """
    IR decoder for the Zaptor36 protocol.
    """
    irp = (
        '{36k,330,msb}<-1,1|1,-1>([T=0][T=1],8,-6,2,D:8,T:1,S:7,F:8,E:4,C:4,-74m)'
        '{C=(D:4+D:4:4+S:4+S:3:4+8*T+F:4+F:4:4+E)&15}'
    )
    frequency = 36000
    bit_count = 32
    encoding = 'msb'

    _lead_in = [TIMING * 8, -TIMING * 6, TIMING * 2]
    _lead_out = [-74000]
    _bursts = [[-TIMING, TIMING], [TIMING, -TIMING]]

    _has_repeat_lead_out = True

    _code_order = [
        ['D', 8],
        ['S', 7],
        ['F', 8],
        ['E', 4]
    ]

    _parameters = [
        ['D', 0, 7],
        ['T', 8, 8],
        ['S', 9, 15],
        ['F', 16, 23],
        ['E', 24, 27],
        ['CHECKSUM', 28, 31]
    ]
    # [D:0..255,S:0..127,F:0..127,E:0..15]
    encode_parameters = [
        ['device', 0, 255],
        ['sub_device', 0, 127],
        ['function', 0, 255],
        ['extended_function', 0, 15]
    ]

    def _calc_checksum(self, device, sub_device, toggle, function, extended_function):
        # {C=(D:4+D:4:4+S:4+S:3:4+8*T+F:4+F:4:4+E)&15}
        d1 = self._get_bits(device, 0, 3)
        d2 = self._get_bits(device, 4, 7)
        s1 = self._get_bits(sub_device, 0, 3)
        s2 = self._get_bits(sub_device, 4, 6)
        f1 = self._get_bits(function, 0, 3)
        f2 = self._get_bits(function, 4, 7)

        checksum = (d1 + d2 + s1 + s2 + (8 * toggle) + f1 + f2 + extended_function) & 15
        return self._get_bits(checksum, 0, 3)

    def decode(self, data, frequency=0):
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)

        if self._last_code is not None:
            if self._last_code == code:
                if code.toggle == 1:
                    self._last_code.repeat_timer.stop()
                    raise RepeatLeadOut

                return self._last_code

            self._last_code.repeat_timer.stop()

        checksum = self._calc_checksum(
            code.device,
            code.sub_device,
            code.toggle,
            code.function,
            code.extended_function
        )

        if checksum != code.checksum:
            raise DecodeError('Invalid checksum')

        if code.toggle != 0:
            raise DecodeError('Invalid toggle')

        self._last_code = code
        return code

    def encode(self, device, sub_device, function, extended_function, repeat_count=0):
        toggle = 0

        checksum = self._calc_checksum(
            device,
            sub_device,
            toggle,
            function,
            extended_function
        )

        code = self._build_packet(
            list(self._get_timing(device, i) for i in range(8)),
            list(self._get_timing(toggle, i) for i in range(1)),
            list(self._get_timing(sub_device, i) for i in range(7)),
            list(self._get_timing(function, i) for i in range(8)),
            list(self._get_timing(extended_function, i) for i in range(4)),
            list(self._get_timing(checksum, i) for i in range(4)),
        )

        toggle = 1

        checksum = self._calc_checksum(
            device,
            sub_device,
            toggle,
            function,
            extended_function
        )

        lead_out = self._build_packet(
            list(self._get_timing(device, i) for i in range(8)),
            list(self._get_timing(toggle, i) for i in range(1)),
            list(self._get_timing(sub_device, i) for i in range(7)),
            list(self._get_timing(function, i) for i in range(8)),
            list(self._get_timing(extended_function, i) for i in range(4)),
            list(self._get_timing(checksum, i) for i in range(4)),
        )

        params = dict(
            frequency=self.frequency,
            D=device,
            S=sub_device,
            F=function,
            E=extended_function
        )

        code = protocol_base.IRCode(
            self,
            [code[:], lead_out[:]],
            ([code[:]] * (repeat_count + 1)) + [lead_out[:]],
            params,
            repeat_count
        )

        return code

    def _test_decode(self):
        return
        rlc = [
            [
                +889, -889, +889, -889, +1778, -1778, +1778, -889, +889, -889, +889, -1778, +889, -889, +889, -889,
                +889, -889, +889, -889, +889, -889, +889, -89997
            ]
        ]

        params = [dict(function=63, toggle=1, device=8)]

        return protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        return
        params = dict(function=106, toggle=1, device=11)
        protocol_base.IrProtocolBase._test_encode(self, params)


Zaptor36 = Zaptor36()
