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


from . import protocol_base
from .. import utils
from . import DecodeError


# noinspection PyAbstractClass
class Universal(protocol_base.IrProtocolBase):
    """
    IR decoder for unknown protocols.
    """

    def __decode_1(self, norm_data):
        bit_encoding = 'pulsetime'
        bits = []

        bursts = norm_data[2:]
        for i in range(0, len(bursts), 2):
            mark, space = bursts[i], bursts[i + 1]

            if [mark, space] not in bits and [mark, space] != norm_data[-2:]:
                bits += [[mark, space]]

        timings = []

        last_pair = bits[0]

        for i, pair in enumerate(bits[1:]):
            if (
                (pair[0] > 0 > last_pair[0] and pair[1] < 0 < last_pair[1]) or
                (pair[0] < 0 < last_pair[0] and pair[1] > 0 > last_pair[1]) or
                (pair[0] == last_pair[0] * 2 and (
                    pair[1] == last_pair[1] or pair[1] == last_pair[1] * 2)) or
                (pair[1] == last_pair[1] * 2 and (
                    pair[0] == last_pair[0] or pair[0] == last_pair[0] * 2))
            ):
                bit_encoding = 'biphase'
                break

            last_pair = pair

        if bit_encoding == 'biphase':
            if len(bits) > 2:
                for mark_1, space_1 in bits[:]:
                    for mark_2, space_2 in bits:
                        if mark_2 == mark_1 and space_2 == space_1:
                            continue

                        if space_1 == space_2 and abs(mark_2) != abs(space_2):
                            mark = -space_2
                            space = space_2

                        elif mark_1 > abs(space_2) and abs(space_1) > mark_2:
                            mark = space_1 + mark_2
                            space = mark_1 + space_2

                        elif mark_1 < abs(space_2) and abs(space_1) < mark_2:
                            mark = mark_2 + space_1
                            space = space_2 + mark_1

                        elif (
                            mark_1 // space_2 == -2 and
                            space_2 * -2 == mark_1
                        ):
                            mark = mark_1 // 2
                            space = space_2

                        elif (
                            space_1 // mark_2 == -2 and
                            space_1 * -2 == mark_2
                        ):
                            space = space_1 // 2
                            mark = mark_2

                        else:
                            continue

                        if mark == 0 or space == 0:
                            continue

                        if mark < 0 > space or mark > 0 < space:
                            continue

                        if [mark, space] not in timings:
                            timings += [[mark, space]]

                if len(timings) == 1:
                    timings += [[timings[0][1], timings[0][0]]]

                if len(timings) > 2:
                    for mark_1, space_1 in timings:
                        for mark_2, space_2 in timings:
                            if mark_1 == mark_2 and space_1 == space_2:
                                continue

                            if mark_1 == mark_2 or space_1 == space_2:
                                timings.remove([mark_2, space_2])

                if len(timings) > 2:
                    neg_count = 0
                    pos_count = 0

                    for mark, space in timings[:]:
                        if mark < 0:
                            neg_count += 1
                        else:
                            pos_count += 1
                        if [space, mark] not in timings:
                            timings.remove([mark, space])

            e_mark, e_space = timings[0]

            offset = 0
            bursts = norm_data[1:-1]
            for i, timing in enumerate(bursts[:]):

                if timing == e_space or timing == e_mark:
                    continue

                elif timing / e_mark == 2:
                    bursts[i + offset] = e_mark
                    bursts.insert(i + offset, e_mark)
                    offset += 1

                elif timing / e_space == 2:
                    bursts[i + offset] = e_space
                    bursts.insert(i + offset, e_space)
                    offset += 1

                elif timing > 0 < e_mark or timing < 0 > e_mark:
                    timings = [timings[1], timings[0]]
                    bursts[i + offset] = e_mark

                elif timing > 0 < e_space or timing < 0 > e_space:
                    timings = [timings[1], timings[0]]
                    bursts[i + offset] = e_space

            pairs = []
            pair = []
            for item in bursts:
                if pair:
                    if pair[0] == e_mark:
                        if item == e_space:
                            pair += [item]
                            pairs += [pair[:]]
                            del pair[:]
                        else:
                            pair += [e_space]
                            pairs += [pair[:]]
                            del pair[:]
                            pair += [item]

                    elif pair[0] == e_space:
                        if item == e_mark:
                            pair += [item]
                            pairs += [pair[:]]
                            del pair[:]
                        else:
                            pair += [e_mark]
                            pairs += [pair[:]]
                            del pair[:]
                            pair += [item]
                else:
                    pair += [item]

            if pair:
                if len(pair) == 1:
                    if pair[0] == e_mark:
                        pair += [e_space]
                    else:
                        pair += [e_mark]
                pairs += [pair[:]]

            encoding = 'msb'

        else:
            pairs = []
            timings = bits[:2]

            bursts = norm_data[2:]
            for i in range(0, len(bursts), 2):
                mark = norm_data[i]
                space = norm_data[i + 1]

                if [mark, space] in timings:
                    pairs += [[mark, space]]

                elif i + 1 == len(norm_data) - 1:
                    for e_mark, e_space in timings:
                        if mark == e_mark:
                            pairs += [[mark, e_space]]
                            break

            if norm_data[:2] in timings:
                bursts.insert(0, norm_data[:2])

            encoding = 'lsb'

        code = 0

        if encoding == 'lsb':
            for i, pair in enumerate(pairs):
                bit = timings.index(pair)
                code |= bit << i
        else:
            for i in range(len(pairs) - 1, -1, -1):
                pair = pairs[i]
                pos = ~(i - len(pairs))
                bit = timings.index(pair)
                code |= bit << pos

        return code

    @staticmethod
    def __decode_2(norm_data):

        for item in norm_data[:]:
            if norm_data.count(item) == 1:
                norm_data.remove(item)

        if norm_data[0] < 0:
            norm_data = norm_data[1:]

        if norm_data[-1] < 0:
            norm_data = norm_data[:-1]

        diff_time = 3

        last_pause = 0
        last_pulse = 0
        code = 0
        mask = 1
        for i, x in enumerate(norm_data):
            if i % 2:
                diff = max(diff_time, last_pause * 0.2)
                if -diff < x - last_pause < diff:
                    code |= mask
                last_pause = x
            else:
                diff = max(diff_time, last_pulse * 0.2)
                if -diff < x - last_pulse < diff:
                    code |= mask

                last_pulse = x
            mask <<= 1
        code |= mask

        return code

    def decode(self, data: list, frequency: int = 0) -> protocol_base.IRCode:

        if len(data) <= 6:
            raise DecodeError('code not long enough')

        norm_data = utils.clean_code(data[:], self.tolerance)
        norm_data = utils.build_mce_rlc(norm_data)

        try:
            code = self.__decode_1(norm_data[:])
        except:  # NOQA
            import traceback
            traceback.print_exc()
            code = self.__decode_2(norm_data[:])

        params = {'CODE': code, 'frequency': frequency}
        code = protocol_base.IRCode(self, data[:], norm_data, params)
        return code
