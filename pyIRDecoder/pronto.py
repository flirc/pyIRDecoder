# -*- coding: utf-8 -*-
#
# This file is part of EventGhost.
# Copyright © 2005-2019 EventGhost Project <http://www.eventghost.org/>
#
# EventGhost is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# EventGhost is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with EventGhost. If not, see <http://www.gnu.org/licenses/>.

"""
This file is part of the **pyWinMCERemote**
project https://github.com/kdschlosser/pyWinMCERemote

:platform: Windows
:license: GPL version 2 or newer
:synopsis: pronto encoder/decoder

.. moduleauthor:: Kevin Schlosser @kdschlosser <kevin.g.schlosser@gmail.com>
"""


PRONTO_CLOCK = 0.241246
SIGNAL_FREE = 10000
SIGNAL_FREE_RC6 = 2700
RC6_START = [2700, -900, 450, -900, 450, -450, 450, -450, 450, -450]
RC6A_START = [3150, -900, 450, -450, 450, -450, 450, -900, 450]


def rlc_to_pronto(freq, data):
    if freq <= 0:
        freq = 36000

    if not isinstance(data[0], list):
        data = [[], data[:]]

    if len(data) == 1:
        data.insert(0, [])

    pronto_carrier = 1000000.0 / (freq * PRONTO_CLOCK)
    carrier = pronto_carrier * PRONTO_CLOCK

    pronto_data = [
        '0000',
        '%04X' % (int(round(pronto_carrier)),),
        '%04X' % (len(data[0]) / 2,),
        '%04X' % (len(data[1]) / 2,)
    ]

    for rlc in data:
        for val in rlc:
            pronto_data.append(
                '%04X' % (int(abs(val) / carrier),)
            )

    if len(pronto_data) % 2 != 0:
        pronto_data.append('%04X' % (SIGNAL_FREE,))

    return ' '.join(pronto_data)


def generic_to_rlc(pronto_data, n_repeat=0):
    if (
        len(pronto_data) < 6 or
        not (pronto_data[0] == 0x0000 or pronto_data[0] == 0x0100)
    ):  # Raw or Learned
        raise Exception("Invalid Raw data %s" % str(pronto_data))

    pronto_carrier = pronto_data[1]
    if pronto_carrier == 0:
        pronto_carrier = int(1000000 / (36000 * PRONTO_CLOCK))

    pw = float(pronto_carrier) * PRONTO_CLOCK
    first_seq = pronto_data[2]
    repeat_seq = pronto_data[3]

    def _get_sequence(start, sequence_len):
        res = []

        for i in range(start * 2, (start + sequence_len) * 2, 2):
            mark = int(pronto_data[i] * pw)
            space = -int(pronto_data[i + 1] * pw)
            res.extend([mark, space])

        return res

    timings = []

    if first_seq != 0:
        timings += [_get_sequence(2, first_seq)]

    if repeat_seq != 0:
        timings += [_get_sequence(2 + first_seq, repeat_seq)]

    timings += [timings[-1]] * n_repeat
    freq = int(1000000 / (pronto_carrier * PRONTO_CLOCK))

    return freq, timings

#
# def rlc_to_pronto(freq, data):
#     if freq <= 0:
#         freq = 36000
#
#     pronto_carrier = int(1000000 / (freq * PRONTO_CLOCK))
#     carrier = pronto_carrier * PRONTO_CLOCK
#
#     pronto_data = [0x0000, pronto_carrier, 0x0000, 0x0000]
#     for val in data:
#         duration = abs(val)
#         pronto_data.append(round(duration / carrier))
#
#     if len(pronto_data) % 2 != 0:
#         pronto_data.append(SIGNAL_FREE)
#
#     pronto_data[3] = (len(pronto_data)-4) / 2
#     out = '%04X' % int(pronto_data[0])
#     for v in pronto_data[1:]:
#         out = out + ' %04X' % int(v)
#     return out
#
#
# def generic_to_rlc(pronto_data, _):  # n_repeat is ignored for Raw
#     if (
#         len(pronto_data) < 6 or
#         not (pronto_data[0] == 0x0000 or pronto_data[0] == 0x0100)
#     ):  # Raw or Learned
#         raise Exception("Invalid Raw data %s" % str(pronto_data))
#
#     pronto_carrier = pronto_data[1]
#     if pronto_carrier == 0:
#         pronto_carrier = int(1000000 / (36000 * PRONTO_CLOCK))
#
#     pw = pronto_carrier * PRONTO_CLOCK
#     first_seq = 2 * pronto_data[2]
#     repeat_seq = 2 * pronto_data[3]
#     pulse = True
#     repeat_count = 0
#     start = 4
#     done = False
#     index = start
#     sequence = first_seq
#
#     if first_seq == 0:
#         if repeat_seq == 0:
#             return None
#         sequence = repeat_seq
#         repeat_count = 1
#
#     timing_data = []
#     while not done:
#         time = int(pronto_data[index] * pw)
#         if pulse:
#             timing_data.append(time)
#         else:
#             timing_data.append(-time)
#         index = index + 1
#         pulse = not pulse
#
#         if index == start + sequence:
#             if repeat_count == 0:
#                 if repeat_seq != 0:
#                     start += first_seq
#                     sequence = repeat_seq
#                     index = start
#                     pulse = True
#                     repeat_count += 1
#                 else:
#                     done = True
#             elif repeat_count == 1:
#                 done = True
#             else:
#                 index = start
#                 pulse = True
#                 repeat_count += 1
#     freq = int(1000000 / (pronto_carrier * PRONTO_CLOCK))
#
#     return freq, timing_data
#


def encode_bits(data, start, stop, s_false, s_true):
    out = ""
    for i in range(start, stop-1, -1):
        if data & (1 << i) > 0:
            out = out + s_true
        else:
            out = out + s_false
    return out


def zero_one_sequences(string, delay):
    final_data = []
    ind = 0
    n = len(string)
    while True:
        count_up = 0
        count_down = 0
        while ind < n and string[ind] == "0":
            ind += 1

        while ind < n and string[ind] == "1":
            count_up += 1
            ind += 1

        while ind < n and string[ind] == "0":
            count_down += 1
            ind += 1

        final_data.extend([delay*count_up, -delay * count_down])
        if ind >= n:
            break

    if final_data[-1] == 0:
        final_data[-1] = -10000
    else:
        final_data[-1] -= 10000

    return final_data


def rc5_to_rlc(pronto_data, n_repeat=0):
    if len(pronto_data) != 6 or pronto_data[0] != 0x5000:  # CodeType RC5
        raise Exception("Invalid RC5 data %s" % str(pronto_data))

    pronto_carrier = pronto_data[1]
    if pronto_carrier == 0x0000:
        pronto_carrier = int(1000000 / (36000 * PRONTO_CLOCK))

    rc5_string = ''

    for j in range(n_repeat + 1):
        toggle = n_repeat % 2 == 0
        if pronto_data[5] > 63:
            rc5_string += encode_bits(2, 1, 0, '10', '01')
        else:
            rc5_string += encode_bits(3, 1, 0, '10', '01')
        if toggle:
            rc5_string += encode_bits(1, 0, 0, '10', '01')
        else:
            rc5_string += encode_bits(0, 0, 0, '10', '01')

        rc5_string += encode_bits(pronto_data[4], 4, 0, '10', '01')
        rc5_string += encode_bits(pronto_data[5], 5, 0, '10', '01')

    final_data = zero_one_sequences(rc5_string, 900)

    freq = int(1000000 / (pronto_carrier * PRONTO_CLOCK))
    return freq, final_data


def rc5x_to_rlc(pronto_data, n_repeat):
    if (
        not (
            len(pronto_data) == 7 or
            (len(pronto_data) == 8 and pronto_data[7] == 0x0000)
        ) or
        pronto_data[0] != 0x5001
    ):  # CodeType RC5X
        raise Exception("Invalid RC5X data %s" % str(pronto_data))

    pronto_carrier = pronto_data[1]
    if pronto_carrier == 0x0000:
        pronto_carrier = int(1000000/(36000*PRONTO_CLOCK))

    if pronto_data[2] + pronto_data[3] != 2:
        raise Exception("Invalid RC5X data %s" % str(pronto_data))

    rc5x_string = ''

    for j in range(n_repeat+1):
        toggle = n_repeat % 2 == 0
        if pronto_data[5] > 63:
            rc5x_string += encode_bits(2, 1, 0, '10', '01')
        else:
            rc5x_string += encode_bits(3, 1, 0, '10', '01')
        if toggle:
            rc5x_string += encode_bits(1, 0, 0, '10', '01')
        else:
            rc5x_string += encode_bits(0, 0, 0, '10', '01')

        rc5x_string += encode_bits(pronto_data[4], 4, 0, '10', '01')
        rc5x_string += '0000'
        rc5x_string += encode_bits(pronto_data[5], 5, 0, '10', '01')
        rc5x_string += encode_bits(pronto_data[6], 5, 0, '10', '01')

    final_data = zero_one_sequences(rc5x_string, 900)

    freq = int(1000000 / (pronto_carrier * PRONTO_CLOCK))
    return freq, final_data


def rc6_to_rlc(pronto_data, n_repeat):
    if len(pronto_data) != 6 or pronto_data[0] != 0x6000:  # CodeType RC6
        raise Exception("Invalid RC6 data %s" % str(pronto_data))

    pronto_carrier = pronto_data[1]
    if pronto_carrier == 0x0000:
        pronto_carrier = int(1000000 / (36000 * PRONTO_CLOCK))

    if pronto_data[2] + pronto_data[3] != 1:
        raise Exception("Invalid RC6 data %s" % str(pronto_data))

    rc6_string = ""
    for j in range(n_repeat+1):
        toggle = n_repeat % 2 == 0
        rc6_string += '1111110010010101'
        if toggle:
            rc6_string += '1100'
        else:
            rc6_string += '0011'

        rc6_string += encode_bits(pronto_data[4], 7, 0, '01', '10')
        rc6_string += encode_bits(pronto_data[5], 7, 0, '01', '10')

    final_data = zero_one_sequences(rc6_string, 450)

    freq = int(1000000 / (pronto_carrier * PRONTO_CLOCK))
    return freq, final_data


def rc6a_to_rlc(pronto_data, n_repeat):
    if len(pronto_data) != 8 or pronto_data[0] != 0x6001:  # CodeType RC6A
        raise Exception("Invalid RC6A data %s" % str(pronto_data))

    pronto_carrier = pronto_data[1]
    if pronto_carrier == 0x0000:
        pronto_carrier = int(1000000 / (36000 * PRONTO_CLOCK))

    if pronto_data[2] + pronto_data[3] != 2:
        raise Exception("Invalid RC6A data %s" % str(pronto_data))

    rc6a_string = ""
    for j in range(n_repeat+1):
        toggle = n_repeat % 2 == 0
        rc6a_string += '11111110010101001'
        if toggle:
            rc6a_string += '1100'
        else:
            rc6a_string += '0011'
        if pronto_data[4] > 127:
            rc6a_string += encode_bits(1, 0, 0, '01', '10')
            rc6a_string += encode_bits(pronto_data[4], 14, 0, '01', '10')
        else:
            rc6a_string += encode_bits(0, 0, 0, '01', '10')
            rc6a_string += encode_bits(pronto_data[4], 6, 0, '01', '10')

        rc6a_string += encode_bits(pronto_data[5], 7, 0, '01', '10')
        rc6a_string += encode_bits(pronto_data[6], 7, 0, '01', '10')

    final_data = zero_one_sequences(rc6a_string, 450)

    freq = int(1000000 / (pronto_carrier * PRONTO_CLOCK))
    return freq, final_data


handlers = {
    0x0000: generic_to_rlc,
    0x0100: generic_to_rlc,
    0x5000: rc5_to_rlc,
    0x5001: rc5x_to_rlc,
    0x6000: rc6_to_rlc,
    0x6001: rc6a_to_rlc,
}


def pronto_to_rlc(pronto, repeat_count=0):
    pronto_data = list(int(v, 16) for v in pronto.split(" "))
    try:
        handler = handlers[pronto_data[0]]
    except KeyError:
        raise Exception(
            "Don't have a decoder for pronto format %s" % hex(
                pronto_data[0]
            )[2:].upper()
        )

    freq, timings = handler(pronto_data, repeat_count)

    return freq, timings
