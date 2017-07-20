# -*- coding: utf-8 -*-
#
# Copyright 2017, Rambler Digital Solutions
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

import datetime
import importlib
import inspect
import re

import trafaret as t
from trafaret import (
    Any,
    Bool,
    Dict,
    Email,
    Enum,
    Int,
    Key,
    List,
    Mapping,
    String,
)


__all__ = (
    'Any',
    'Bool',
    'Callback',
    'Class',
    'Date',
    'Dict',
    'Email',
    'Enum',
    'Int',
    'Key',
    'List',
    'Mapping',
    'String',
    'TimeDelta',

    'cast_interval',
)


class Date(t.Trafaret):

    def check_value(self, value):
        if not isinstance(value, datetime.date):
            self._failure('value should be a date', value=value)

    def __repr__(self):
        return '<Date>'


class TimeDelta(t.Trafaret):

    def check_value(self, value):
        if not isinstance(value, datetime.timedelta):
            self._failure('value should be a timedelta', value=value)

    def __repr__(self):
        return '<TimeDelta>'


class Importable(t.Trafaret):

    def check_and_return(self, value):
        if not isinstance(value, str):
            self._failure('value should be a string', value=value)

        if ':' not in value:
            self._failure('import notation must be in format:'
                          ' `package.module:target`', value=value)

        module, object_name = value.split(':', 1)

        try:
            mod = importlib.import_module(module)
        except ImportError as exc:
            self._failure(str(exc), value=value)
        else:
            try:
                return getattr(mod, object_name)
            except AttributeError as exc:
                self._failure(str(exc), value=value)

    def __repr__(self):
        return '<Importable>'


class Class(Importable):

    def check_and_return(self, value):
        if inspect.isclass(value):
            return value
        value = super(Class, self).check_and_return(value)
        if not inspect.isclass(value):
            self._failure('imported value should be a class, got %s' % value,
                          value=value)
        return value

    def __repr__(self):
        return '<Class>'


class Callback(Importable):

    def check_and_return(self, value):
        if inspect.isfunction(value):
            return value
        value = super(Callback, self).check_and_return(value)
        if not callable(value):
            self._failure('imported value should be a callable, got %s'
                          '' % value, value=value)
        return value

    def __repr__(self):
        return '<Callback>'


def cast_interval(value):
    """Casts interval value into `datetime.timedelta` instance.

    If value is `int`, returned `timedelta` get constructed from a given
    by the value`s seconds.

    If value is `str`, then it get converted into seconds according the rules:

    - ``\d+s`` - time delta in seconds. Example: ``10s`` for 10 seconds;
    - ``\d+m`` - time delta in minutes. Example: ``42m`` for 42 minutes;
    - ``\d+h`` - time delta in hours. Example: ``1h`` for 1 hour;
    - ``\d+d`` - time delta in days. Example: ``10d`` for 10 days.

    :param str | int | datetime.timedelta value: An interval value.
    :rtype: datetime.timedelta
    """
    if isinstance(value, str):
        match = re.match(r'^(-)?(\d+)([dhms])$', value)
        if match is not None:
            has_neg_sign, value, unit = match.groups()
            value = int(value)
            value *= {
                's': 1,
                'm': 60,
                'h': 60 * 60,
                'd': 60 * 60 * 24,
            }[unit]
            value *= -1 if has_neg_sign else 1
    if isinstance(value, int):
        value = datetime.timedelta(seconds=value)
    elif not isinstance(value, datetime.timedelta):
        raise t.DataError('invalid interval value %s' % value)
    return value