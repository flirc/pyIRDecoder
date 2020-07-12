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


TIMING = 444


class RC6M32(protocol_base.IrProtocolBase):
    """
    IR decoder for the RC6M32 protocol.
    """
    __name__ = 'RC6-m-32'

    irp = '{36k,444,msb}<-1,1|1,-1>(6,-2,1:1,M:3,<-2,2|2,-2>(1-(T:1)),OEM1:8,OEM2:8,D:8,F:8,^107m)*'
    frequency = 36000
    bit_count = 37
    encoding = 'msb'

    _lead_in = [TIMING * 6, -TIMING * 2]
    _lead_out = [107000]
    _middle_timings = [{'start': 4, 'stop': 5, 'bursts': [[-TIMING * 2, TIMING * 2], [TIMING * 2, -TIMING * 2]]}]
    _bursts = [[-TIMING, TIMING], [TIMING, -TIMING]]

    _code_order = [
        ['M', 3],
        ['OEM1', 8],
        ['OEM2', 8],
        ['D', 8],
        ['F', 8]
    ]

    _parameters = [
        ['C0', 0, 0],
        ['M', 1, 3],
        ['T', 4, 4],
        ['OEM1', 5, 12],
        ['OEM2', 13, 20],
        ['D', 21, 28],
        ['F', 29, 36],
    ]
    # [OEM1:0..255,OEM2:0..255,D:0..255,F:0..255,M:0..7,T@:0..1=0]
    encode_parameters = [
        ['mode', 0, 7],
        ['device', 0, 255],
        ['function', 0, 255],
        ['oem1', 0, 255],
        ['oem2', 0, 255]
    ]

    def decode(self, data, frequency=0):
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)

        if self._last_code is not None:
            if (
                self._last_code == code and
                self._last_code.toggle == code.toggle
            ):
                return self._last_code

            last_code = self._last_code
            self._last_code.repeat_timer.stop()

            if last_code == code:
                raise RepeatLeadOut

        if code.c0 != 1:
            raise DecodeError('Checksum failed')

        if code.mode == 6 and code.oem1 == 128:
            raise DecodeError('RC6632 protocol')

        self._last_code = code
        return code

    def encode(self, mode, device, function, oem1, oem2, repeat_count=0):
        c0 = 1

        packet = self._build_packet(
            list(self._get_timing(c0, i) for i in range(1)),
            list(self._get_timing(mode, i) for i in range(3)),
            [-TIMING * 2, TIMING * 2],
            list(self._get_timing(oem1, i) for i in range(8)),
            list(self._get_timing(oem2, i) for i in range(8)),
            list(self._get_timing(device, i) for i in range(8)),
            list(self._get_timing(function, i) for i in range(8)),
        )

        lead_out = self._build_packet(
            list(self._get_timing(c0, i) for i in range(1)),
            list(self._get_timing(mode, i) for i in range(3)),
            [TIMING * 2, -TIMING * 2],
            list(self._get_timing(oem1, i) for i in range(8)),
            list(self._get_timing(oem2, i) for i in range(8)),
            list(self._get_timing(device, i) for i in range(8)),
            list(self._get_timing(function, i) for i in range(8)),
        )

        params = dict(
            frequency=self.frequency,
            M=mode,
            D=device,
            F=function,
            OEM1=oem1,
            OEM2=oem2
        )

        code = protocol_base.IRCode(
            self,
            [packet[:], lead_out[:]],
            ([packet[:]] * (repeat_count + 1)) + [lead_out[:]],
            params,
            repeat_count
        )

        return code

    def _test_decode(self):
        rlc = [[
            2664, -888, 444, -444, 444, -444, 444, -888, 444, -888, 888, -444, 444, -444,
            444, -444, 444, -444, 888, -888, 444, -444, 888, -444, 444, -888, 444, -444, 444, -444,
            888, -888, 444, -444, 888, -888, 888, -888, 444, -444, 888, -888, 888, -444, 444, -888,
            444, -444, 444, -444, 444, -444, 444, -444, 444, -444, 444, -444, 888, -70148,
        ]]

        params = [dict(function=1, toggle=0, device=75, oem2=137, oem1=9, mode=6)]

        return protocol_base.IrProtocolBase._test_decode(self, rlc, params)

    def _test_encode(self):
        params = dict(function=1, toggle=0, device=75, oem2=137, oem1=9, mode=6)
        protocol_base.IrProtocolBase._test_encode(self, params)


RC6M32 = RC6M32()
