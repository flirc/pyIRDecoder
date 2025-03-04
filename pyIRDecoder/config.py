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


from . import xml_handler
import os


class Config(object):
    def __init__(self, path=None):
        self._database_url = 'http://eventghost.net:43847'

        if path is None:
            self._xml = xml_handler.XMLRootElement('IRConfig')
        else:
            path = os.path.expandvars(path)
            path = os.path.abspath(path)
            self._xml = xml_handler.load(path, 'IRConfig')

        self._path = path

        if 'database_url' in self._xml:
            self._database_url = self._xml.database_url
        else:
            self._xml.database_url = self._database_url

        self._parent = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        if value:
            value = os.path.expandvars(value)
            value = os.path.abspath(value)
        self._path = value

    @property
    def database_url(self):
        return self._database_url

    @database_url.setter
    def database_url(self, value):
        print('setting database_url:', value)
        self._database_url = value

    def __getattr__(self, item):
        if item == 'database_url':
            # noinspection PyArgumentList
            return self.__class__.database_url.fget(self)

        if item in self.__dict__:
            return self.__dict__[item]

        return getattr(self._xml, item)

    def __setattr__(self, key, value):
        if key in ('_xml', '_database_url', 'database_url'):
            object.__setattr__(self, key, value)
        else:
            setattr(self._xml, key, value)

    def __len__(self):
        return len(self._xml)

    def __iter__(self):
        return iter(self._xml)

    def __delitem__(self, key):
        self._xml.__delitem__(key)

    def __delattr__(self, item):
        self._xml.__delattr__(item)

    def __str__(self):
        return str(self._xml)

    def save(self, path=None):
        if self._parent is None:
            raise RuntimeError(
                'Config instance is not attached to an IRDecoder instance'
            )
        if path is None:
            path = self.path
        else:
            path = os.path.expandvars(path)
            path = os.path.abspath(path)

        if path is None:
            raise RuntimeError(
                'You must supply a path to save the config file to.'
            )

        for i, decoder in enumerate(self._parent):
            self._xml.pop(i)
            xml = decoder.xml
            self._xml.insert(i, xml)

        self._xml.database_url = self._database_url

        self._xml.xml_file = path
        self._xml.save()
        self._xml.write_file()
