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

from pyIRDecoder import (
    RepeatLeadInError, 
    RepeatLeadOutError,
    IRException
)
from pyIRDecoder import protocols

protocol = protocols.Entone


class Entone(object):
    rlc = [[
        2664, -888, 444, -444, 444, -444, 444, -888, 444, -888, 1332,
        -444, 444, -444, 444, -888, 444, -444, 888, -444, 444, -888, 444,
        -444, 444, -444, 444, -444, 444, -444, 444, -444, 444, -444, 888,
        -444, 444, -444, 444, -888, 444, -444, 888, -888, 888, -444, 444,
        -888, 888, -444, 444, -444, 444, -444, 444, -444, 444, -444, 444,
        -444, 444, -444, 444, -444, 444, -444, 444, -444, 444, -444, 444,
        -444, 444, -444, 444, -444, 444, -444, 444, -444, 444, -444, 444,
        -444, 444, -444, 444, -444, 444, -444, 444, -444, 444, -888, 888,
        -444, 444, -444, 444, -888, 444, -444, 444, -444, 444, -444, 444,
        -444, 444, -131000
    ]]

    params = [dict(function=238)]


def test_decode():
    for rlc, params in zip(Entone.rlc, Entone.params):
        try:
            ir_code = protocol.decode(rlc, protocol.frequency)
        except (RepeatLeadInError, RepeatLeadOutError):
            if params is not None:
                raise
            continue
        
        for key, value in params.items():
            assert getattr(ir_code, key) == value, (
                key,
                getattr(ir_code, key),
                value
            )
        print()
        print(ir_code)


def test_encode():
    for params in Entone.params:
        if params is None:
            continue

        ir_code = protocol.encode(**params)
        for key, value in params.items():
            assert getattr(ir_code, key) == value, (
                key,
                getattr(ir_code, key),
                value
            )

        new_ir_code = None
        for rlc in ir_code.normalized_rlc:
            try:
                new_ir_code = protocol.decode(rlc, protocol.frequency)
            except (RepeatLeadInError, RepeatLeadOutError):
                continue
            except IRException:
                new_ir_code = protocol.decode(
                    ir_code.original_rlc,
                    protocol.frequency
                )
                break

        print()
        print(ir_code)
        print(new_ir_code)
        
        assert new_ir_code == ir_code

        break
