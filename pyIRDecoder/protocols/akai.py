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


TIMING = 289


class Akai(protocol_base.IrProtocolBase):
    """
    IR decoder for the Akai protocol.
    """
    irp = '{38k,289,lsb}<1,-2.6|1,-6.3>(D:3,F:7,1,^25.3m)*'
    frequency = 38000
    bit_count = 10
    encoding = 'lsb'

    _lead_out = [TIMING, 25300]
    _bursts = [
        [TIMING, -int(round(TIMING * 2.6))],
        [TIMING, -int(round(TIMING * 6.3))]
    ]

    _code_order = [
        ['D', 3],
        ['F', 7]
    ]

    _parameters = [
        ['D', 0, 2],
        ['F', 3, 9],
    ]
    # [D:0..7,F:0..127]
    encode_parameters = [
        ['device', 0, 7],
        ['function', 0, 127],
    ]

    def encode(
        self,
        device: int,
        function: int,
        repeat_count: int = 0
    ) -> protocol_base.IRCode:
        packet = self._build_packet(
            D=device,
            F=function
        )

        params = dict(
            frequency=self.frequency,
            D=device,
            F=function
        )

        code = protocol_base.IRCode(
            self,
            packet[:] * (repeat_count + 1),
            [packet[:]] * (repeat_count + 1),
            params,
            repeat_count
        )
        return code
