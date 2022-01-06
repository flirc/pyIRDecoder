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
from . import DecodeError

TIMING = 432


class Fujitsu56(protocol_base.IrProtocolBase):
    """
    IR decoder for the Fujitsu56 protocol.
    """
    irp = (
        '{37k,432,lsb}<1,-1|1,-3>'
        '(8,-4,20:8,99:8,0:4,E:4,D:8,S:8,X:8,F:8,1,-110)*'
    )
    frequency = 37000
    bit_count = 56
    encoding = 'lsb'

    _lead_in = [TIMING * 8, -TIMING * 4]
    _lead_out = [TIMING, -TIMING * 110]
    _middle_timings = []
    _bursts = [[TIMING, -TIMING], [TIMING, -TIMING * 3]]

    _code_order = [
        ['E', 4],
        ['D', 8],
        ['S', 8],
        ['X', 8],
        ['F', 8]
    ]

    _parameters = [
        ['C0', 0, 7],
        ['C1', 8, 15],
        ['C2', 16, 19],
        ['E', 20, 23],
        ['D', 24, 31],
        ['S', 32, 39],
        ['X', 40, 47],
        ['F', 48, 55]
    ]
    # [D:0..255,S:0..255=D,F:0..255,E:0..15=0,X:0..255=0]
    encode_parameters = [
        ['device', 0, 255],
        ['sub_device', 0, 255],
        ['function', 0, 255],
        ['extended_function', 0, 15],
        ['x', 0, 255]
    ]

    def decode(self, data: list, frequency: int = 0) -> protocol_base.IRCode:
        code = protocol_base.IrProtocolBase.decode(self, data, frequency)
        if self._last_code is not None:
            if self._last_code == code:
                return self._last_code

            self._last_code.repeat_timer.stop()
            self._last_code = None

        if code.c0 != 20 or code.c1 != 99 or code.c2 != 0:
            raise DecodeError('Checksum failed')

        self._last_code = code

        return code

    @classmethod
    def encode(
        cls,
        device: int,
        sub_device: int,
        function: int,
        extended_function: int,
        x: int,
        repeat_count: int = 0
    ) -> protocol_base.IRCode:
        c0 = 20
        c1 = 99
        c2 = 0

        packet = cls._build_packet(
            C0=c0,
            C1=c1,
            C2=c2,
            E=extended_function,
            D=device,
            S=sub_device,
            X=x,
            F=function
        )

        params = dict(
            frequency=cls.frequency,
            D=device,
            S=sub_device,
            F=function,
            E=extended_function,
            X=x
        )

        code = protocol_base.IRCode(
            cls(),
            packet[:] * (repeat_count + 1),
            [packet[:]] * (repeat_count + 1),
            params,
            repeat_count
        )

        return code
