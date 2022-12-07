#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import xbmc
from resources.lib.proxy import Proxy
from resources.lib.addon import *
from resources.lib.log import LOG
from resources.lib.cache import Cache

if __name__ == '__main__':
  proxy = Proxy()
  proxy.start()
  LOG('proxyname: {}'.format(proxy.proxyname))
  cache = Cache(profile_dir)
  cache.save_file('proxy.conf', proxy.proxyname)

  monitor = xbmc.Monitor()
  while not monitor.abortRequested():
    if monitor.waitForAbort(1):
      break

  proxy.stop()
