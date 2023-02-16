#!/usr/bin/env python
# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division

from datetime import datetime

weekdays = ['Dom', 'Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab']

def timestamp2str(timestamp, format='%H:%M'):
  time = datetime.fromtimestamp(timestamp / 1000)
  if '%a' in format:
    w = int(time.strftime('%w'))
    format = format.replace('%a', weekdays[w])
  return time.strftime(format).capitalize()
