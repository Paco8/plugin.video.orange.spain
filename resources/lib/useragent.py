#!/usr/bin/env python
# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division
import random

FIREFOX_VERSIONS = ['140.0', '141.0', '142.0']
FIREFOX_PLATFORMS = [
  'X11; Linux x86_64; rv:{v}',
  'Windows NT 10.0; Win64; x64; rv:{v}',
  'Macintosh; Intel Mac OS X 10.15; rv:{v}',
]

def firefox_ua():
  v = random.choice(FIREFOX_VERSIONS)
  p = random.choice(FIREFOX_PLATFORMS).format(v=v)
  return 'Mozilla/5.0 ({}) Gecko/20100101 Firefox/{}'.format(p, v)

useragent = firefox_ua()
