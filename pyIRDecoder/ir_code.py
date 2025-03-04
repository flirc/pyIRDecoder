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

from . import high_precision_timers
from . import thread_worker
from . import pronto
from . import utils
from . import xml_handler
from . import integer_wrapper


_timer_thread_worker = thread_worker.TimerThreadWorker()
_process_thread_worker = thread_worker.ProcessThreadWorker()


class Timer(object):
    def __init__(self, func, duration):
        self.func = func
        self._duration = duration
        self._adjusted_duration = duration
        self.timer = high_precision_timers.TimerUS()

    @property
    def duration(self):
        return self._duration

    @property
    def adjusted_duration(self):
        return self._adjusted_duration

    def run_func(self):
        if self.timer is None:
            return True

        if self.timer.elapsed() >= self.adjusted_duration:
            _process_thread_worker.add(self.func)
            return True

        return False

    def stop(self):
        if self.timer is not None:
            self.timer = None
            _process_thread_worker.add(self.func)

    def start(self, timer):
        self._adjusted_duration = (
            self.duration +
            (self.duration * 0.20) +
            (timer.elapsed() * 4)
        )
        if self.timer is None:
            self.timer = high_precision_timers.TimerUS()

        self.timer.reset()
        _timer_thread_worker.add(self)

    def cancel(self):
        self.timer = None

    @property
    def is_running(self):
        return self.timer.elapsed() < self.adjusted_duration


# noinspection PyProtectedMember
class IRCode(object):

    def __init__(
        self,
        decoder,
        original_rlc,
        normalized_rlc,
        data,
        repeat_count=-1,
        name=None
    ):
        if not isinstance(normalized_rlc[0], list):
            normalized_rlc = [normalized_rlc]

        self._decoder = decoder
        self._original_rlc = original_rlc
        self._normalized_rlc = normalized_rlc
        self._code = None
        self._name = name
        self._xml = None
        self._int = None
        self._hex = None
        self._callbacks = []
        self._repeat_count = repeat_count

        self._data = {}

        for key, value in data.items():
            if (
                key != 'frequency' and
                not isinstance(value, integer_wrapper.IntegerWrapper)
            ):
                for name, start, stop in decoder._parameters:
                    if name == key:
                        value = integer_wrapper.IntegerWrapper(
                            value,
                            stop + 1 - start,
                            decoder._bursts,
                            decoder.encoding
                        )
            self._data[key] = value

        if decoder.repeat_timeout == 0:
            repeat_timeout = sum(
                abs(item) for rlc in normalized_rlc for item in rlc
            )
        else:
            repeat_timeout = decoder.repeat_timeout

        self._repeat_timer = Timer(self.__repeat_reset, repeat_timeout)
        self._repeat_duration = repeat_timeout
        self.bind_released_callback(decoder.reset)

        #if self._name is None:
            #_process_thread_worker.add(self.__set_name)

    def __iter__(self):
        for item in self.normalized_rlc:
            yield item[:]

    def __repr__(self):
        mapping = {
            'M': 'mode',
            'D': 'device',
            'F': 'function',
            'S': 'sub_device',
            'E': 'extended_function',
        }
        params = []

        for param, _ in self._decoder._code_order:
            value = self._data[param]
            param = mapping.get(param, param.lower())
            params += [param + '=' + str(value)]

        return 'IrCode(' + ', '.join(params) + ')'

    @property
    def repeat_count(self):
        return self._repeat_count

    @repeat_count.setter
    def repeat_count(self, value):
        self._repeat_count = value

    def __repeat_reset(self):
        for callback in self._callbacks[:]:
            callback(self)

    def bind_released_callback(self, callback):
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unbind_released_callback(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def save(self):
        if self not in self.decoder._saved_codes:
            self.decoder._saved_codes.append(self)

    def delete(self):
        if self in self.decoder._saved_codes:
            self.decoder._saved_codes.remove(self)

    def __set_name(self):
        config = self.decoder.config

        if config is None:
            return

        url = self.decoder.config.database_url

        if not url:
            return

        import requests

        try:
            response = requests.get(url)
            if response.status_code != 200:
                raise requests.ConnectionError
        except requests.ConnectionError:
            return
        else:
            token = response.content
            response = requests.get(
                url + token + '/get_name',
                params=dict(
                    decoder=self.decoder.name,
                    code=self.hexadecimal
                )
            )
            if response.status_code != 200:
                return
            else:
                self._name = response.content

    @staticmethod
    def load_from_xml(xml, decoder):
        """
        :param xml:
        :type xml: xml_handler.XMLElement
        :return:
        """

        params = {k.upper(): v for k, v in xml.attrib.items()}

        name = params.pop('NAME')
        params['frequency'] = params.pop('FREQUENCY')
        params.pop('DECODER')
        original_rlc = list(
            int(item) for item in xml.OriginalRLC.text.split(', ')
        )
        normalized_rlc = list(
            int(item) for item in xml.NormalizedRLC.text.split(', ')
        )

        self = IRCode(decoder, original_rlc, normalized_rlc, params, name=name)

        self._xml = xml
        return self

    @property
    def xml(self):
        if self._xml is None:
            self._xml = xml_handler.XMLElement(
                'IRCode',
                decoder=self.decoder.name,
                **self._data
            )
            xml = xml_handler.XMLElement('OriginalRLC')
            text = []

            for item in self._original_rlc:
                if item > 0:
                    text += ['+' + str(item)]
                else:
                    text += [str(item)]

            xml.text = ', '.join(text)

            self._xml.OriginalRLC = xml

            xml = xml_handler.XMLElement('NormalizedRLC')
            text = []

            for item in self._normalized_rlc:
                if item > 0:
                    text += ['+' + str(item)]
                else:
                    text += [str(item)]

            xml.text = ', '.join(text)

            self._xml.NormalizedRLC = xml

        self._xml.name = self.name

        return self._xml

    @property
    def repeat_timer(self):
        return self._repeat_timer

    @property
    def params(self):
        res = []

        for key in (
            'mode',
            'n',
            'h',
            'oem'
            'oem1',
            'oem2',
            'device',
            'device2',
            'device3',
            'pair_id',
            'sub_device',
            'extended_function',
            'function',
            'g',
            'x',
            'code'
        ):
            try:
                if getattr(self, key) is not None:
                    res += [key]
            except AttributeError:
                continue

        for key in sorted(list(self._data.keys())):
            for char in list('MDFSECTXOHGN'):
                if key.upper().startswith(char):
                    break
            else:
                res += [key.lower()]

        if 'T' in self._data:
            res += ['toggle']

        return res

    @property
    def decoder(self):
        return self._decoder

    @property
    def frequency(self):
        return self._data['frequency']

    @property
    def original_rlc(self):
        return self._original_rlc[:]

    @property
    def normalized_rlc(self):
        return self._normalized_rlc[:]

    @property
    def original_rlc_pronto(self):
        code = [abs(item) for item in self._original_rlc]
        return pronto.rlc_to_pronto(self.frequency, code)

    @property
    def normalized_rlc_pronto(self):
        code = [abs(item) for rlc in self._normalized_rlc for item in rlc]
        return pronto.rlc_to_pronto(self.frequency, code)

    @property
    def original_rlc_mce(self):
        code = utils.build_mce_rlc(self._original_rlc)
        return code

    @property
    def original_mce_pronto(self):
        code = [abs(item) for item in self.original_mce_rlc]
        return pronto.rlc_to_pronto(self.frequency, code)

    @property
    def normalized_rlc_mce(self):
        code = [
            item for rlc in self._normalized_rlc
            for item in utils.build_mce_rlc(rlc[:])
        ]
        return code

    @property
    def normalized_mce_pronto(self):
        code = [abs(item) for item in self.normalized_rlc_mcs]
        return pronto.rlc_to_pronto(self.frequency, code)

    @property
    def device(self):
        return self._data.get('D', None)

    @property
    def sub_device(self):
        return self._data.get('S', None)

    @property
    def function(self):
        return self._data.get('F', None)

    @property
    def toggle(self):
        return self._data.get('T', None)

    @property
    def mode(self):
        return self._data.get('M', None)

    @property
    def n(self):
        return self._data.get('N', None)

    @property
    def g(self):
        return self._data.get('G', None)

    @property
    def address(self):
        return self._data.get('A', None)

    @property
    def x(self):
        return self._data.get('X', None)

    @property
    def extended_function(self):
        return self._data.get('E', None)

    @property
    def checksum(self):
        return self._data.get('CHECKSUM', None)

    @property
    def u(self):
        return self._data.get('U', None)

    @property
    def oem(self):
        return self._data.get('OEM', None)

    @property
    def oem1(self):
        return self._data.get('OEM1', None)

    @property
    def oem2(self):
        return self._data.get('OEM2', None)

    def __iadd__(self, other):
        if not isinstance(other, IRCode):
            raise TypeError

        other._normalized_rlc += self._normalized_rlc
        other._original_rlc += self.original_rlc
        other._data.update(self._data)
        return other

    def __add__(self, other):
        if not isinstance(other, IRCode):
            raise TypeError

        self._normalized_rlc += other.normalized_rlc
        self._original_rlc += other.original_rlc
        self._data.update(other._data)
        return self

    def __radd__(self, other):
        if not isinstance(other, IRCode):
            raise TypeError

        self._normalized_rlc += other.normalized_rlc
        self._original_rlc += other.original_rlc
        self._data.update(other._data)
        return self

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]

        if item.upper() in self._data:
            return self._data[item.upper()]

        raise AttributeError(item)

    def __int__(self):
        if self._int is None:
            bits = ''

            if 'CODE' in self._data:
                if 'M' in self._data:
                    bits += bin(self.mode)[2:].zfill(3)[:3]

                bits += bin(self.code)[2:]
            else:
                for param, num_bits in self._decoder._code_order:
                    bts = bin(int(self._data[param]))[2:].zfill(num_bits)[:num_bits]
                    if self._decoder.encoding == 'msb':
                        bits += bts
                    else:
                        for i in range(num_bits - 1, -1, -1):
                            bits += bts[i]

            self._int = int(bits, 2)
        return self._int

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def hexadecimal(self):
        if self._hex is None:
            res = hex(int(self))[2:].upper().rstrip('L')
            self._hex = '0x' + res.zfill(len(res) + (len(res) % 2))
        return self._hex

    def __eq__(self, other):
        if isinstance(other, list):
            if isinstance(other[0], list):
                if len(other) != len(self._normalized_rlc):
                    return False

                for i in range(len(other)):
                    rlc1 = other[i]
                    rlc2 = self._normalized_rlc[i]

                    if len(rlc1) != len(rlc2):
                        return False

                    for j in range(len(rlc1)):
                        if not self.decoder._match(rlc1[j], rlc2[j]):
                            return False
            else:
                if len(self._normalized_rlc) > 1:
                    return False
                if len(self._normalized_rlc[0]) != len(other):
                    return False

                for i in range(len(other)):
                    if not self.decoder._match(
                        other[i],
                        self._normalized_rlc[0][i]
                    ):
                        return False

            return True

        if isinstance(other, IRCode):
            if other.decoder.__class__ != self.decoder.__class__:
                return False

            return str(other) == str(self)

        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        if self._name is None:
            res = []

            if 'CODE' in self._data:
                if 'M' in self._data:
                    h = hex(int(self.mode))[2:].upper()
                    h = h.zfill(len(h) + (len(h) % 2))
                    res += [h]

                h = hex(int(self.code))[2:].upper()
                h = h.zfill(len(h) + (len(h) % 2)).rstrip('L')
                res += [h]
            else:
                for param, num_bits in self._decoder._code_order:
                    value = int(self._data[param])
                    fill = (num_bits // 8) + 1
                    fill += fill % 2

                    res += [(('%X' % (value,)).zfill(fill)).rstrip('L')]

            return self.decoder.name + '.' + ':'.join(res)

        return self._name
