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

# Local imports
from . import protocol_base
from . import DecodeError, RepeatLeadInError


TIMING = 268


class Amino(protocol_base.IrProtocolBase):
    """
    IR decoder for the Amino protocol.
    """
    irp = (
        '{37.3k,268,msb}<-1,1|1,-1>'
        '([T=1][T=0],7,-6,3,D:4,1:1,T:1,1:2,0:8,F:8,15:4,C:4,-79m)+'
        '{C=(D:4+4*T+9+F:4+F:4:4+15)&15}'
    )

    frequency = 37300
    bit_count = 32
    encoding = 'msb'

    _lead_in = [TIMING * 7, -TIMING * 6, TIMING * 3]
    _lead_out = [-79000]
    _bursts = [[-TIMING, TIMING], [TIMING, -TIMING]]

    _code_order = [
        ['D', 4],
        ['F', 8]
    ]

    _parameters = [
        ['D', 0, 3],
        ['C0', 4, 4],  # 1
        ['T', 5, 5],
        ['C1', 6, 7],  # 1
        ['C2', 8, 15],  # 0
        ['F', 16, 23],
        ['C3', 24, 27],  # 15
        ['CHECKSUM', 28, 31]
    ]
    # [D:0..15,F:0..255]
    encode_parameters = [
        ['device', 0, 15],
        ['function', 0, 255],
    ]

    @staticmethod
    def _calc_checksum(
        device: protocol_base.IntegerWrapper,
        function: protocol_base.IntegerWrapper,
        toggle: protocol_base.IntegerWrapper,
        c3: protocol_base.IntegerWrapper
    ) -> protocol_base.IntegerWrapper:
        # (D:4+4*T+9+F:4+F:4:4+15)&15}
        d = device[:4:0]
        f1 = function[:4:0]
        f2 = function[:4:4]

        return ((d + 4 * toggle + 9 + f1 + f2 + c3) & c3)[:4:0]

    def decode(self, data: list, frequency: int = 0) -> protocol_base.IRCode:
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)

        checksum = self._calc_checksum(
            code.device,
            code.function,
            code.toggle,
            code.c3
        )

        if (
            checksum != code.checksum or
            code.c0 != 1 or
            code.c1 != 1 or
            code.c2 != 0
        ):
            raise DecodeError('Checksum failed')

        if self._last_code is not None:
            if (
                self._last_code == code and
                self._last_code.toggle == code.toggle
            ):
                return self._last_code

            self._last_code.repeat_timer.stop()

        if code.toggle == 1:
            raise RepeatLeadInError

        self._last_code = code
        return code

    def encode(
        self,
        device: int,
        function: int,
        repeat_count: int = 0
    ) -> protocol_base.IRCode:
        device = protocol_base.IntegerWrapper(
            device,
            4,
            self._bursts,
            self.encoding
        )
        function = protocol_base.IntegerWrapper(
            function,
            8,
            self._bursts,
            self.encoding
        )

        c3 = protocol_base.IntegerWrapper(
            15,
            4,
            self._bursts,
            self.encoding
        )
        toggle = protocol_base.IntegerWrapper(
            1,
            1,
            self._bursts,
            self.encoding
        )

        checksum = self._calc_checksum(
            device,
            function,
            toggle,
            c3
        )

        packet1 = self._build_packet(
            D=device,
            C0=1,
            T=toggle,
            C1=1,
            C2=0,
            F=function,
            C3=c3,
            CHECKSUM=checksum
        )

        toggle = protocol_base.IntegerWrapper(
            0,
            1,
            self._bursts,
            self.encoding
        )

        checksum = self._calc_checksum(
            device,
            function,
            toggle,
            c3
        )

        packet2 = self._build_packet(
            D=device,
            C0=1,
            T=toggle,
            C1=1,
            C2=0,
            F=function,
            C3=c3,
            CHECKSUM=checksum
        )

        packet = [packet1]
        packet += [packet2] * (repeat_count + 1)

        params = dict(
            frequency=self.frequency,
            D=device,
            F=function
        )

        code = protocol_base.IRCode(
            self,
            packet1[:] + (packet2[:] * (repeat_count + 1)),
            [packet1[:]] + ([packet2[:]] * (repeat_count + 1)),
            params,
            repeat_count
        )
        return code
