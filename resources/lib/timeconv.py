#!/usr/bin/env python
# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division

from datetime import datetime

def my_strftime(time, format):
  weekdays = ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab']
  if '%a' in format:
    w = int(time.strftime('%w'))
    format = format.replace('%a', weekdays[w])
  return time.strftime(format)

def timestamp2str(timestamp, format='%H:%M'):
  time = datetime.fromtimestamp(timestamp / 1000)
  return my_strftime(time, format)
