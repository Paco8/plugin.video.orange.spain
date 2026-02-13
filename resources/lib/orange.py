# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division

import sys
import io
import os
import requests
import json
import re
import time

from .b64 import encode_base64, decode_base64
from .log import LOG, print_json
from .network import Network
from .cache import Cache
from .timeconv import *
from .endpoints import endpoints, API_IMAGES
from .useragent import useragent

def date2str(timestamp, format='%d/%m/%Y %H:%M:%S'):
  return timestamp2str(timestamp, format)

class Orange(object):
    username = ''
    password = ''

    users = []

    cookie = ''
    device = {'id': '', 'type': 'SmartTV'}
    profile_id = None
    hd_devices = ['SmartTV', 'SmartTV_Android', 'FireTV', 'Chromecast', 'GoogleStick', 'AKS19']

    add_extra_info = False

    def __init__(self, config_directory):
      # Network
      headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Origin': 'https://orangetv.orange.es',
        'Referer': 'https://orangetv.orange.es/',
        'User-Agent': useragent,
        #'User-Agent': 'okhttp/4.10.0',
      }
      self.net = Network()
      self.net.headers = headers

      # Cache
      self.cache = Cache(config_directory)

      if not os.path.exists(config_directory + 'cache'):
        os.makedirs(config_directory + 'cache')

      # Accounts
      data = self.cache.load_file('accounts.json')
      if data:
        self.users = json.loads(data)

      # User
      data = self.cache.load_file('user.json')
      if data:
        u = json.loads(data)
        self.username = u['username']
        self.password = u['password']

      # Profile
      data = self.cache.load_file('profile_id.conf')
      if data:
        self.profile_id = data

      self.logged = self.login()
      if not self.logged:
        return

      self.entitlements = self.get_entitlements()
      self.subscribed_channels = self.get_subscribed_channels()

      # Device
      data = self.cache.load_file(self.username + '_device.json')
      if data:
        self.device = json.loads(data)
      device = self.get_preferred_device()
      if device['id'] != self.device['id']:
        self.device['id'] = device['serial_number']
        self.device['type'] = device['type']
        self.cache.save_file(self.username + '_device.json', json.dumps(self.device, ensure_ascii=False))

      # Search
      data = self.cache.load_file('searchs.json')
      self.search_list = json.loads(data) if data else []

    def load_json(self, url, check_errors = True):
      #print(url)
      headers = self.net.headers.copy()
      headers['Cookie'] = self.cookie
      #print_json(headers)
      content = self.net.load_url(url, headers)
      if not content and check_errors:
         raise Exception('No se ha obtenido respuesta')
      data = json.loads(content)
      if check_errors and ('response' in data) and ('status' in data['response']) and data['response']['status'] == 'FAILURE':
         raise Exception(data['response']['message'])
      return data

    def get_license_url(self):
      l = {'SmartTV': 'https://smarttv.orangetv.orange.es/stv/api/rtv/v1/drm',
           'FireTV': 'https://firetv.orangetv.orange.es/stv/api/rtv/v1/drm',
           'PC': 'https://pc.orangetv.orange.es/pc/api/rtv/v1/widevinedrm',
           'Smartphone_Android': 'https://android.orangetv.orange.es/mob/api/rtv/v1/drm',
           'Tablet_Android': 'https://android.orangetv.orange.es/mob/api/rtv/v1/drm',
           'SmartTV': 'https://smarttv.orangetv.orange.es/stv/api/rtv/v1/drm',
           'Chromecast': 'https://cc.orangetv.orange.es/stv/api/rtv/v1/drm',
           'GoogleStick': 'https://smarttv.orangetv.orange.es/stv/api/rtv/v1/drm',
           'AKS19': 'https://stb.orangetv.orange.es/stb/api/rtv/v1/drm'}
      #print_json(l)
      return l.get(self.device['type'], 'https://pc.orangetv.orange.es/pc/api/rtv/v1/widevinedrm')

    def change_user(self, username):
      for u in self.users:
        if u['username'] == username:
          self.username = u['username']
          self.password = u['password']
          self.cache.save_file('user.json', json.dumps(u, ensure_ascii=False))
          self.cache.remove_file('cookie.conf')
          self.cache.remove_file('entitlements.json')
          self.cache.remove_file('subscribed_channels.json')
          self.cache.remove_file('bouquet.json')
          self.cache.remove_file('channels2.json')
          self.cache.remove_file('subscription.json')
          self.cache.remove_file('profile_id.conf')
          return

    def add_user(self, username, password):
      u = {'username': username, 'password': encode_base64(password)}
      self.users.append(u)
      self.cache.save_file('accounts.json', json.dumps(self.users, ensure_ascii=False))

    def remove_user(self, username):
      nl = []
      for u in self.users:
        if u['username'] != username: nl.append(u)
      self.users = nl
      self.cache.save_file('accounts.json', json.dumps(self.users, ensure_ascii=False))

    def change_device(self, serial_number):
      for dev in self.get_devices():
        if dev['serial_number'] == serial_number:
          self.device['type'] = dev['type']
          self.device['id'] = serial_number
          self.cache.save_file(self.username + '_device.json', json.dumps(self.device, ensure_ascii=False))
          self.cache.remove_file('channels2.json')
          break;

    def get_devices(self, use_cache=False):
      cache_filename = self.username + '_device_list.json'
      content = self.cache.load(cache_filename)
      if content and use_cache:
        data = json.loads(content)
      else:
        url = endpoints['get-terminal-list']
        data = self.load_json(url)
        self.cache.save_file(cache_filename, json.dumps(data, ensure_ascii=False))
      #print_json(data)
      household_id = data['response']['householdId']
      self.cache.save_file('household_id.conf', str(household_id))
      res = []
      for t in data['response']['terminals']:
        dev = {}
        dev['id'] = t['id']
        dev['serial_number'] = t['serialNumber']
        dev['name'] = t['name']
        dev['type'] = t['model']['externalId']
        dev['reg_date'] = date2str(t['registrationDate'])
        res.append(dev)
      return res

    def find_device_type(self, device_list, device_type):
      for dev in device_list:
        if dev['type'] == device_type:
          return dev
      return None

    def get_preferred_device(self):
      devices = self.get_devices(use_cache=True)
      dev = None

      for dev in devices:
        if self.device['id'] == dev['serial_number']:
          return dev

      for dev in devices:
        if dev['type'] in self.hd_devices:
          return dev

      if len(devices) < 5:
        self.register_device()
        devices = self.get_devices()
        for dev in devices:
          if dev['type'] in self.hd_devices:
            return dev

      # Not found
      if not dev:
        dev = devices[0]
      return dev

    def get_serial_number(self):
      serial_number = ''
      data = self.get_devices()
      for t in data:
        if t['type'] == self.device['type']:
          serial_number = t['serial_number']
          break;
      return serial_number

    def create_serial_number(self, device_type = 'SmartTV'):
      def random_str(length=64):
        import random
        s = ''
        for _ in range(0, length): s += random.choice('ABCDEF0123456789')
        return s
      def uuid_str():
        import uuid
        return str(uuid.uuid4()).upper()

      serial_number = ''
      if   device_type == 'SmartTV':
        serial_number = 'OTVATV' + random_str()
      elif device_type == 'FireTV':
        serial_number = 'OTVAMZ' + random_str()
      elif device_type in ['Smartphone_Android', 'Tablet_Android']:
        serial_number = random_str(12) + '_' + uuid_str()
      elif device_type == 'Chromecast':
        serial_number = random_str(32)
      else:
        serial_number = uuid_str()
      return serial_number

    def register_device(self, serial_number = None, name = None, device_type = 'SmartTV'):
      if not serial_number:
        serial_number = self.create_serial_number(device_type)
      if not name:
        name = device_type +' '+ serial_number[:8]
      url = endpoints['register-terminal'].format(serial_number=serial_number, name=name, model_external_id=device_type)
      data = self.load_json(url)
      return data

    def unregister_device(self, serial_number):
      url = endpoints['unregister-terminal'].format(serial_number=serial_number)
      data = self.load_json(url)
      return data

    def get_entitlements(self):
      content = self.cache.load_file('entitlements.json')
      if content:
        data = json.loads(content)
      else:
        url = endpoints['get-service-list']
        data = self.load_json(url)
        self.cache.save_file('entitlements.json', json.dumps(data, ensure_ascii=False))

      res = []
      for i in data['response']:
        if i['model'] == 'SVOD':
          res.append(i['externalId'])
      return res

    def is_subscribed_vod(self, products, service_key='serviceExternalId'):
      if len(products) == 0: return True
      for p in products:
        if p[service_key] in self.entitlements:
          return True
      return False

    def create_slug(self, name):
      import unicodedata
      nfkd = unicodedata.normalize('NFKD', name)
      t = nfkd.encode('ASCII', 'ignore').lower()
      t = t.decode('utf-8')
      t = re.sub(r'\W+', '-', t).strip('-')
      return t

    def find_cover(self, images):
      cover = ''

      for i in images:
        if i['name'] == 'VERTICAL':
           cover = API_IMAGES + i['value']
           break

      return cover

    def get_art(self, images, kvalue = 'value'):
      art = {}

      base_url = API_IMAGES
      for i in images:
        if i['name'] == 'VERTICAL':
           art['poster'] = base_url + i[kvalue]
           art['fanart'] = art['poster']
        elif i['name'] == 'cover_4_3' or i['name'] == 'COVER5_1' or i['name'] == 'APP_SLSHOW_3':
           if not 'thumb' in art:
             art['thumb'] = base_url + i[kvalue]
             art['icon'] = art['thumb']
        elif i['name'] == 'cover_16_9':
           art['landscape'] = base_url + i[kvalue]

      if not 'poster' in art:
        if 'thumb' in art: art['poster'] = art['thumb']
        elif 'landscape' in art: art['poster'] = art['landscape']
        if 'poster' in art: art['fanart'] = art['poster']

      return art

    def get_contributors(self, data):
      director = []
      cast = []
      for c in data:
        name = c['firstName'] +' '+ c['lastName']
        if   c['role'] == 'DIR': director.append(name)
        elif c['role'] == 'ACT': cast.append(name)
      return director, cast

    def get_country(self, data):
      country = []
      for c in data: country.append(c['code'])
      return country

    def get_genre(self, data):
      genre = []
      for c in data: genre.append(c['name'])
      return genre

    def get_video_info(self, id):
      url = endpoints['get-video'].format(external_id=id)
      data = self.load_json(url)
      #LOG(json.dumps(data, indent=4))
      return data

    def get_aggregated_video_info(self, id):
      url = endpoints['get-aggregated-video'].format(external_asset_id=id)
      data = self.load_json(url)
      return data

    def add_video_extra_info(self, t):
      try:
        if not 'info' in t: t['info'] = {}
        if not 'art' in t: t['art'] = {}
        if not ('info_id' in t and 'stream_type' in t): return

        if t['stream_type'] == 'rec':
          self.add_recording_extra_info(t['info_id'], t)
        elif t['stream_type'] == 'tv':
          self.add_live_extra_info(t['info_id'], t)
        else:
          self.add_vod_extra_info(t['info_id'], t)
      except:
        pass

    def add_vod_extra_info(self, id, t):
      filename = 'cache/INF_' + id + '.json'
      content = self.cache.load(filename)
      if content:
        data = json.loads(content)
      else:
        url = endpoints['get-video-asset'].format(external_id=id)
        data = self.load_json(url)
        self.cache.save_file(filename, json.dumps(data, ensure_ascii=False))

      data = data['response']
      #print_json(data)

      if not 'title' in t['info']: t['info']['title'] = data['name']
      if len(t['art']) == 0:
        t['art'] = self.get_art(data['attachments'])
      t['info']['duration'] = data['duration'] / 1000
      t['info']['plot'] = data['description']
      t['info']['year'] = data['year']
      t['info']['director'], t['info']['cast'] = self.get_contributors(data['contributors'])
      t['info']['country'] = self.get_country(data['countries'])
      t['info']['genre'] = self.get_genre(data['genreEntityList'])
      if 'prName' in data: t['info']['mpaa'] = data['prName'].replace('ML_', '')

    def get_title(self, data):
      t = {}
      t['info'] = {}
      t['id'] = ''
      if data['contentType'] == 'Movie':
        t['type'] = 'movie'
        #t['stream_type'] = 'vod'
        t['info']['title'] = data['name']
        t['info']['mediatype'] = 'movie'
        #LOG(json.dumps(data, indent=4))
        if len(data['availabilities']) > 0:
          t['id'] = data['availabilities'][0]['videoId']
          t['availability'] = {'start': data['availabilities'][0].get('startTime'), 'end': data['availabilities'][0].get('endTime')}
        else:
          try:
            d = self.get_aggregated_video_info(data['externalContentId'])
            if 'uniqueVideos' in d['response']:
              t['id'] = d['response']['uniqueVideos'][0]['externalId']
          except:
            pass
          #t['stream_type'] = 'u7d'
        t['stream_type'] = 'u7d' if t['id'].startswith('U7D') else 'vod'
        t['art'] = self.get_art(data['images'])
        if t['stream_type'] == 'vod':
          t['subscribed'] = len(data['availabilities']) > 0
        elif t['stream_type'] == 'u7d':
          if 'sourceChannelId' in data:
            t['subscribed'] = self.is_subscribed_channel(data['sourceChannelId'])
        if 'externalContentId' in data:
          t['info_id'] = data['externalContentId']
          t['wl_id'] = t['info_id']
        t['slug'] = self.create_slug(t['info']['title'])
        if self.add_extra_info:
          self.add_video_extra_info(t)
      elif data['contentType'] == 'Season':
        t['type'] = 'series'
        t['info']['title'] = data['seriesName']
        t['info']['mediatype'] = 'tvshow'
        t['id'] = data['externalSeriesId']
        t['art'] = self.get_art(data['seriesImages'])
        t['info']['plot'] = ''
        if 'externalContentId' in data: t['wl_id'] = data['externalContentId']

      if 'prName' in data: t['info']['mpaa'] = data['prName'].replace('ML_', '')
      if 'rating' in data: t['info']['rating'] = data['rating']
      if t['id'] != '':
        t['url'] = 'https://orangetv.orange.es/vps/dyn/' + t['id'] + '?bci=otv-2'

      return t

    def get_wishlist(self):
      res = []

      url = endpoints['get-profile-wishlist']
      data = self.load_json(url)
      #self.save_file('/tmp/wishlist.json', json.dumps(data, ensure_ascii=False))

      for d in data['response']:
        t = self.get_title(d)
        if t['id'] != '':
          res.append(t)

      return res

    def add_recording_extra_info(self, id, t):
      filename = 'cache/RECINF_' + id + '.json'
      content = self.cache.load(filename)
      if content:
        data = json.loads(content)
      else:
        url = endpoints['get-extended-program-list'].format(ext_program_channel_ids=id)
        data = self.load_json(url)
        self.cache.save_file(filename, json.dumps(data, ensure_ascii=False))

      data = data['response'][0]

      if not 'title' in t['info']: t['info']['title'] = data['name']
      t['art'] = self.get_art(data['attachments'])
      t['info']['plot'] = data['description']
      t['info']['year'] = data['year']
      t['info']['director'], t['info']['cast'] = self.get_contributors(data['contributors'])
      t['info']['country'] = self.get_country(data['countries'])
      t['info']['genre'] = self.get_genre(data['genreEntityList'])
      if 'prName' in data: t['info']['mpaa'] = data['prName'].replace('ML_', '')

    def get_recordings(self):
      res = []

      url = endpoints['get-recording-ticket-list']
      data = self.load_json(url)
      self.cache.save_file('recordings.json', json.dumps(data, ensure_ascii=False))
      #LOG(json.dumps(data, indent=4))

      for d in data['response']:
        t = {}
        t['info'] = {}
        t['art'] = {}
        t['type'] = 'movie'
        t['stream_type'] = 'rec'
        t['info']['title'] = d['name']
        t['info']['mediatype'] = 'movie'
        t['id'] = str(d['id'])
        t['cover'] = ''
        t['info']['plot'] = d['description']
        t['info']['duration'] = (d['endDate'] - d['startDate']) / 1000;
        t['url'] = 'https://orangetv.orange.es/vps/rec/' + t['id'] + '?bci=otv-3'
        t['slug'] = self.create_slug(t['info']['title'])
        t['start_date'] = date2str(d['startDate'], '%d/%m/%Y')
        t['end_date'] = date2str(d['windowEnd'], '%d/%m/%Y')
        t['availability'] = {'start': d['startDate'], 'end': d['windowEnd']}
        t['info']['aired'] = date2str(d['startDate'], '%Y-%m-%d')
        if d['startDate'] > (time.time() * 1000):
          t['info']['title'] += ' ('+ t['start_date'] +')'
          t['info']['title'] = '[COLOR red]'+ t['info']['title'] +'[/COLOR]'
        t['info_id'] = d['programExternalId']
        if 'prName' in d: t['info']['mpaa'] = d['prName'].replace('ML_', '')
        if self.add_extra_info:
          self.add_video_extra_info(t)
        t['info']['plot'] += '\n[COLOR blue]Exp: ' + t['end_date'] + '[/COLOR]'

        res.append(t)

      return res

    def order_recording(self, program_id, recursive=False):
      url = endpoints['get-extended-program'].format(program_external_id=program_id)
      data = self.load_json(url)
      id = data['response']['id']
      url = endpoints['order-recording'].format(program_id=id, recursive='true' if recursive else 'false')
      data = self.load_json(url)
      return data

    def delete_recording(self, recording_id):
      url = endpoints['delete-recording'].format(recording_id=recording_id)
      data = self.load_json(url)
      return data

    def add_to_wishlist(self, id):
      url = endpoints['add-to-wishlist'].format(id=id)
      data = self.load_json(url)
      return data

    def remove_from_wishlist(self, id):
      url = endpoints['remove-from-wishlist'].format(id=id)
      data = self.load_json(url)
      return data

    def get_seasons(self, id):
      res = []

      url = endpoints['get-tvshow-season-list'].format(series_external_id=id)

      data = self.load_json(url)
      #print_json(data)
      #self.cache.save_file('seasons.json', json.dumps(data, ensure_ascii=False))

      for d in data['response']:
        t = {}
        t['id'] = d['externalId']
        t['info'] = {}
        t['type'] = 'season'
        t['info']['title'] = d['name']
        t['info']['mediatype'] = 'season'
        t['info']['season'] = d['seasonNumber']
        t['info']['tvshowtitle'] = d['seriesName']
        t['info']['plot'] = d['description']
        t['info']['plotoutline'] = d['shortDescription']
        t['info']['year'] = d['year']
        t['art'] = self.get_art(d['attachments'])
        t['info']['director'], t['info']['cast'] = self.get_contributors(d['contributors'])
        t['info']['country'] = self.get_country(d['countries'])
        t['info']['genre'] = self.get_genre(d['genres'])
        if 'prName' in d: t['info']['mpaa'] = d['prName'].replace('ML_', '')

        res.append(t)

      return res

    def get_episodes(self, id):
      res = []

      url = endpoints['get-tvshow-episode-list'].format(season_external_id=id)
      data = self.load_json(url)
      #print_json(data)
      #Orange.save_file('/tmp/episodes.json', json.dumps(data, ensure_ascii=False))

      for d in data['response']:
        t = {}
        t['id'] = d['uniqueVideos'][0]['externalId']
        t['availability'] = {'start': d.get('windowStart'), 'end': d['uniqueVideos'][0].get('removalDate')}
        t['info'] = {}
        #t['type'] = 'episode'
        t['type'] = 'movie'
        t['stream_type'] = 'u7d' if t['id'].startswith('U7D') else 'vod'
        t['info']['title'] = d['name']
        t['info']['mediatype'] = 'episode'
        t['info']['season'] = d['tvShowReference']['seasonNumber']
        t['info']['episode'] = d['tvShowReference']['episodeNumber']
        t['info']['tvshowtitle'] = d['tvShowReference']['seriesName']
        t['info']['plot'] = d['description']
        t['info']['year'] = d['year']
        t['info']['duration'] = d['duration'] / 1000
        t['info']['genre'] = self.get_genre(d['genreEntityList'])
        t['art'] = self.get_art(d['attachments'])
        t['url'] = 'https://orangetv.orange.es/vps/dyn/' + t['id'] + '?bci=otv-2'
        t['slug'] = self.create_slug(t['info']['tvshowtitle'])
        t['subscribed'] = self.is_subscribed_vod(d['uniqueVideos'][0]['securityGroups'], 'externalId')
        if 'prName' in d: t['info']['mpaa'] = d['prName'].replace('ML_', '')

        res.append(t)

      return res

    def get_category_list(self, id):
      res = []

      filename = 'cache/CAT_' + id + '.json'
      content = self.cache.load(filename)
      if content:
        data = json.loads(content)
      else:
        url = endpoints['get-unified-list'].format(external_category_id=id)
        data = self.load_json(url)
        self.cache.save_file(filename, json.dumps(data, ensure_ascii=False))
      #Orange.save_file('/tmp/list.json', content)

      for d in data['response']:
        t = {}
        t['info'] = {}
        if d['template'] == 'SeriesFolder':
          # Serie
          t['type'] = 'series'
          t['info']['mediatype'] = 'tvshow'
          t['info']['title'] = d['tvShowSeries']['name']
          t['id'] = d['tvShowSeries']['externalId']
          t['info']['plot'] = d['tvShowSeries']['description']
          t['art'] = self.get_art(d['tvShowSeries']['attachments'])
          t['subscribed'] = self.is_subscribed_vod(d['securityGroups'], 'externalId')
          t['wl_id'] = t['id']
        elif d['template'] == 'Heading':
          t['type'] = 'category'
          t['id'] = d['externalId']
          t['info']['title'] = d['name']
          if 'extrafields' in d:
            for f in d['extrafields']:
              if f.get('name') == 'EntryPoint_Param':
                if f.get('value') != '': t['entry_point'] = f.get('value')
        elif d['template'] == 'Members':
          videos = self.get_category_list(d['externalId'])
          for v in videos: res.append(v)
          continue
        elif d['template'] == 'SVOD_SERVICE':
          # Movie
          t['type'] = 'movie'
          t['stream_type'] = 'u7d' if d['contentProvider'] == 'U7D' else 'vod'
          t['info']['title'] = d['name']
          t['info']['mediatype'] = 'movie'
          t['id'] = d['externalId']
          t['info']['year'] = d['year']
          t['info']['duration'] = d['duration'] / 1000
          t['info']['plot'] = d['description']
          t['info']['genre'] = self.get_genre(d['genreEntityList'])
          t['availability'] = {'start': d.get('windowStart'), 'end': d.get('removalDate')}
          t['art'] = self.get_art(d['attachments'])
          if 'assetExternalId' in d:
            t['info_id'] = d['assetExternalId']
            t['wl_id'] = t['info_id']

          # self.add_video_extra_info(t)
          t['subscribed'] = self.is_subscribed_vod(d['securityGroups'], 'externalId')
          t['slug'] = self.create_slug(t['info']['title'])
        else:
          LOG('Unsupported template: {}'.format(d['template']))
          continue

        if 'prName' in d: t['info']['mpaa'] = d['prName'].replace('ML_', '')
        t['url'] = 'https://orangetv.orange.es/vps/dyn/' + t['id'] + '?bci=otv-2'
        res.append(t)

      return res

    def get_category_list2(self, id):
      subdata = self.get_subscription_info()
      headers = self.net.headers.copy()
      headers['Cookie'] =  self.cookie
      url = endpoints['browsing']

      data = {
        'services': ','.join(self.entitlements),
        'tvpacks': subdata['tvpacks'],
        'bouquet_id': subdata['bouquet'],
        'channels': ','.join(self.subscribed_channels),
        'sp': subdata['offer'],
        'myTeam': 'NA',
        'available_sp': subdata['available_sp'],
        'from': 0,
        'count': 999,
        'external_id': id,
        'resolution': 'SD,HD',
        'device_type': 'PC',
      }
      #print_json(data)
      response = self.net.session.post(url, headers=headers, json=data)
      content = response.content.decode('utf-8')
      #Orange.save_file('/tmp/browse.json', content)
      data = json.loads(content)

      res = []
      for d in data.get('elements', []):
        if d['type'] in ['movie', 'serie']:
          t = {'info': {}, 'type': 'movie'}
          t['info']['title'] = d['name']
          t['info']['mediatype'] = 'movie'
          t['id'] = d['actions'][0]['entryPoint'].rsplit('/', 1)[-1]
          t['info']['plot'] = d['metadata']['description']
          t['art'] = {'poster': API_IMAGES + d['image']}
          if d['type'] == 'movie':
            t['type'] = 'movie'
            t['stream_type'] = 'u7d' if 'U7D' in t['id'] else 'vod'
            t['info']['mediatype'] = 'movie'
            if 'assetExternalId' in d:
              t['info_id'] = d['assetExternalId']
              t['wl_id'] = t['info_id']
          else:
            t['type'] = 'series'
            t['info']['mediatype'] = 'tvshow'
            t['info_id'] = d['seriesExternalId']
            t['wl_id'] = t['info_id']
          res.append(t)
      for d in data.get('rows', []):
        if d['type'] in ['horizontal', 'vertical']:
          t = {'info': {}, 'type': 'category', 'id': d['id'], 'info':{'title': d['title']}}
          res.append(t)
      return res

    def search_live(self, search_term):
      res = []
      url = endpoints['search-live'].format(text=search_term, device_models=self.device['type'])
      url += '&channels=' + ','.join(self.subscribed_channels)
      data = self.load_json(url)
      #self.cache.save_file('search_live.json', json.dumps(data, ensure_ascii=False))
      #print_json(data)

      for d in data['response']:
        t = {}
        t['info'] = {}
        t['art'] = {}
        t['type'] = 'movie'
        t['stream_type'] = 'tv'
        t['is_catchup'] = True
        t['info']['mediatype'] = 'movie'
        t['search_id'] = d['id']
        t['id'] = d['externalChannelId']
        t['channel_name'] = d['channelName']
        t['program_id'] = d['availabilities'][0]['externalId']
        t['info']['title'] = d['name']
        t['start_date'] = date2str(int(d['broadcastStartTime']), '%d/%m/%Y')
        t['end_date'] = date2str(int(d['broadcastEndTime']), '%d/%m/%Y')
        t['info']['duration'] = (int(d['broadcastEndTime']) - int(d['broadcastStartTime'])) / 1000
        t['info']['aired'] = date2str(int(d['broadcastStartTime']), '%Y-%m-%d')
        t['info']['title'] += ' [' + t['channel_name'] +'] ('+ t['start_date'] +')'
        if int(d['broadcastStartTime']) > (time.time() * 1000):
          t['info']['title'] = '[COLOR red]'+ t['info']['title'] +'[/COLOR]'
        if 'images' in d:
          t['art'] = self.get_art(d['images'], 'url')
        t['subscribed'] = self.is_subscribed_channel(d['externalChannelId'])
        t['slug'] = self.create_slug(t['info']['title'])
        res.append(t)

      return res

    def search_vod(self, search_term, content_type):
      res = []
      url = endpoints['search-vod'].format(text=search_term, content_type=content_type, services=','.join(self.entitlements))
      data = self.load_json(url)
      #self.cache.save_file('search_vod.json', json.dumps(data, ensure_ascii=False))
      #print_json(data)

      for d in data['response']:
        t = {}
        t['info'] = {}
        t['art'] = {}
        if d['contentType'] == 'movie':
          t['type'] = 'movie'
          t['info']['mediatype'] = 'movie'
          t['id'] = d['availabilities'][0]['externalId']
          t['stream_type'] = 'u7d' if t['id'].startswith('U7D') else 'vod'
          t['info']['title'] = d['name']
          t['info']['year'] = d['year']
          t['url'] = 'https://orangetv.orange.es/vps/dyn/' + t['id'] + '?bci=otv-2'
          t['art'] = self.get_art(d['images'], 'url')
          if 'externalId' in d:
            t['info_id'] = d['externalId']
            t['wl_id'] = t['info_id']
          if t['stream_type'] == 'vod':
            t['subscribed'] = self.is_subscribed_vod(d['availabilities'])
          elif t['stream_type'] == 'u7d':
            t['subscribed'] = self.is_subscribed_channel(d['sourceChannelId'])
          t['slug'] = self.create_slug(t['info']['title'])
          if self.add_extra_info:
            self.add_video_extra_info(t)
          res.append(t)
        elif d['contentType'] == 'season':
          t['type'] = 'series'
          t['info']['mediatype'] = 'tvshow'
          t['info']['title'] = d['seriesName']
          t['id'] = d['seriesExternalId']
          t['info']['year'] = d['year']
          t['url'] = 'https://orangetv.orange.es/vps/dyn/' + t['id'] + '?bci=otv-2'
          if 'parentImages' in d:
            t['art'] = self.get_art(d['parentImages'], 'url')
          t['subscribed'] = self.is_subscribed_vod(d['availabilities'])
          t['wl_id'] = t['id']
          """
          t['type'] = 'season'
          t['info']['mediatype'] = 'season'
          t['info']['title'] = d['name']
          t['info']['tvshowtitle'] = d['seriesName']
          t['id'] = d['externalId']
          t['info']['year'] = d['year']
          t['art'] = self.get_art(d['images'], 'url')
          """
          res.append(t)

      return res

    def download_epg(self, datestr=None):
      from datetime import datetime,timedelta

      if not datestr:
        cache_filename = 'epg.json'
        date = datetime.today()
        days = 2
        hours = []
        for n in range(0, days):
          datestr = date.strftime('%Y%m%d')
          hours += [datestr+ '_8h_1', datestr + '_8h_2', datestr + '_8h_3']
          date += timedelta(days=1)
      else:
        cache_filename = 'cache/epg_' + datestr + '.json'
        hours = [datestr+ '_8h_1', datestr + '_8h_2', datestr + '_8h_3']

      content = self.cache.load(cache_filename, 12*60)
      if content:
        return json.loads(content)

      epg = {}
      for h in hours:
        filename = h + '.json'
        #url = 'https://epg.orangetv.orange.es/epg/Smartphone_Android/3_PRO/' + filename
        url = 'https://epg.orangetv.orange.es/epg/Smartphone_Android/1_PRO/' + filename
        #LOG(url)
        data = self.load_json(url)

        #print(data)

        for ch in data:
          id = ch['channelExternalId']
          if not id in epg: epg[id] = []
          for p in ch['programs']:
            epg[id].append(p)

      self.cache.save_file(cache_filename, json.dumps(epg, ensure_ascii=False))
      return epg

    def get_epg(self, date=None):
      from datetime import datetime
      channels = self.download_epg(date)
      epg = {}
      for id in channels:
        if not id in epg: epg[id] = []
        last_id = -1
        for p in channels[id]:
          if p['id'] == last_id: continue
          last_id = p['id']
          program = {}
          program['startDate'] = p['startDate']
          program['endDate'] = p['endDate']
          program['start_str'] = date2str(program['startDate'], "%H:%M")
          program['date_str'] = date2str(program['startDate'], "%a %d %H:%M")
          program['end_str'] = date2str(program['endDate'], "%H:%M")
          program['name'] = p['name']
          descs = program['name'].split(' - ')
          program['desc1'] = descs[0]
          program['desc2'] = descs[1] if len(descs) > 1 else ''
          program['description'] = p['description']
          program['attachments'] = p['attachments']
          if len(program['attachments']) > 0:
            program['art'] = {'poster': API_IMAGES + program['attachments'][0]['value']}
          program['program_id'] = p['referenceProgramId']
          program['id'] = p['id']
          program['channel_id'] = id
          if 'genres' in p:
            program['genres'] = []
            for g in p['genres']:
              program['genres'].append(g['name'])
          program['series'] = {'season': p.get('seriesSeason'), 'episode': p.get('episodeId'), 'name': p.get('seriesName')}
          epg[id].append(program)
      return epg

    def find_program_epg(self, epg, id, timestamp):
      if id in epg:
        for p in epg[id]:
          #print(p)
          if (p['startDate'] <= timestamp) and (timestamp <= p['endDate']):
            return p
      return None

    def colorize_title(self, title):
      s = title['info']['title']

      stype = title.get('stream_type')
      #if stype == 'u7d': s += ' (U7D)'
      #elif stype == 'rec': s += ' (REC)'

      source_type = title.get('source_type')
      if source_type:
        if source_type not in ['SmoothStreaming', 'MPEGDash', 'HLS']:
          s += ' ('+ source_type + ')'
        if source_type == 'SmoothStreaming':
          s = '[COLOR cyan]' + s +'[/COLOR]'
        elif source_type != 'MPEGDash':
          s = '[COLOR blue]' + s +'[/COLOR]'

      color1 = 'yellow'
      color2 = 'red'

      if not title.get('subscribed', True):
        color1 = 'gray'
        color2 = 'gray'
        s = '[COLOR gray]' + s +'[/COLOR]'
      elif 'startDate' in title:
        aired = (title['startDate'] <= (time.time() * 1000))
        if not aired:
          color1 = 'blue'
          color2 = 'blue'
          s = '[COLOR blue]' + s +'[/COLOR]'
      if title.get('desc1', '') != '':
        s += ' - [COLOR {}]{}[/COLOR]'.format(color1, title['desc1'])
      if title.get('desc2', '') != '':
        s += ' - [COLOR {}]{}[/COLOR]'.format(color2, title['desc2'])
      return s

    def add_epg_info(self, channels, epg, timestamp):
      from datetime import datetime

      for ch in channels:
        program = self.find_program_epg(epg, ch['id'], timestamp)
        if program is not None:
          ch['desc1'] = program['desc1']
          if 'desc2' in program: ch['desc2'] = program['desc2']
          ch['info']['plot'] = "{} ({}-{})\n{}".format(program['name'], program['start_str'], program['end_str'], program['description'])
          if len(program['attachments']) > 0:
            ch['art']['poster'] = API_IMAGES + program['attachments'][0]['value']
          ch['program_id'] = program['program_id']
          ch['recording_id'] = program['id']
          ch['startDate'] = program['startDate']
          ch['endDate'] = program['endDate']
          ch['series'] = program['series']

    def get_subscribed_channels(self):
      content = self.cache.load('subscribed_channels.json')
      if content:
        data = json.loads(content)
      else:
        url = endpoints['get-subscribed-channels']
        data = self.load_json(url)
        self.cache.save_file('subscribed_channels.json', json.dumps(data, ensure_ascii=False))

      res = []
      for i in data['response']:
        res.append(i['externalChannelId'])
      return res

    def is_subscribed_channel(self, id):
      return id in self.subscribed_channels

    """
    def get_channels_list(self):
      res = []
      url = endpoints['get-profile-channel-list']
      data = self.load_json(url)

      for d in data['response']:
        t = {}
        t['info'] = {}
        t['art'] = {}
        t['type'] = 'movie'
        t['stream_type'] = 'tv'
        t['info']['mediatype'] = 'movie'
        t['info']['title'] = d['name']
        t['id'] = d['id']
        #LOG(json.dumps(d, indent=4))
        res.append(t)

      return res
    """

    def download_bouquet(self):
      url = endpoints['get-bouquet-list']
      data = self.load_json(url)
      return data

    def get_subscription_info(self):
      content = self.cache.load('subscription.json')
      if content:
        return json.loads(content)

      url = endpoints['get-household']
      data = self.load_json(url)
      client_id = data['response']['username']

      url = endpoints['get-client-data'].format(client_code=client_id)
      data = self.load_json(url)
      client_data = json.loads(data['response'])

      url = endpoints['get-household-subscription']
      data = self.load_json(url)
      service_plan = data['response']['servicePlanSubscriptionInfoList'][0]['servicePlan']
      packages = service_plan['channelPackages']
      packs = []
      for p in packages:
        packs.append(p['externalId'])
      tvpacks = ','.join(packs)
      res = {'client_id': client_id, 'tvpacks': tvpacks,
              'bouquet': service_plan['bouquets'][0]['externalId'],
              'offer': service_plan['externalId'],
              'available_sp': client_data['available_sp']}
      self.cache.save_file('subscription.json', json.dumps(res, ensure_ascii=False))
      return res

    def download_channels(self, bouquet):
      url = endpoints['get-channel-list'].format(bouquet_id=bouquet, model_external_id=self.device['type'])
      headers = self.net.headers.copy()
      headers['Cookie'] = self.cookie
      response = self.net.session.get(url, headers=headers)
      content = response.content.decode('utf-8')
      data = json.loads(content)

      # Get response cookies
      cookie_dict = requests.utils.dict_from_cookiejar(response.cookies)
      response_cookie = '; '.join([key + '=' + value for key, value in cookie_dict.items()])
      return data, response_cookie

    def download_subscribed_channels(self):
      url = endpoints['get-subscribed-channels']
      headers = self.net.headers.copy()
      headers['Cookie'] = self.cookie
      response = self.net.session.get(url, headers=headers)
      content = response.content.decode('utf-8')
      data = json.loads(content)

      # Get response cookies
      cookie_dict = requests.utils.dict_from_cookiejar(response.cookies)
      response_cookie = '; '.join([key + '=' + value for key, value in cookie_dict.items()])
      return data, response_cookie

    def get_channels_list(self):
      res = []

      content = self.cache.load('bouquet.json')
      if content:
        data = json.loads(content)
      else:
        data = self.download_bouquet()
        self.cache.save_file('bouquet.json', json.dumps(data, ensure_ascii=False))

      #LOG(json.dumps(data, indent=4))
      bouquet = data['response'][0]['id']

      content = self.cache.load('channels2.json')
      if content:
        data = json.loads(content)
      else:
        data, _ = self.download_channels(bouquet)
        self.cache.save_file('channels2.json', json.dumps(data, ensure_ascii=False))

      for d in data['response']:
        t = {}
        t['info'] = {}
        t['art'] = {}
        t['type'] = 'movie'
        t['stream_type'] = 'tv'
        t['info']['mediatype'] = 'movie'
        t['id'] = d['id'] = d['externalChannelId']
        t['dial'] = d['number']
        t['info']['title'] = str(t['dial']) +'. '+ d['name']
        t['channel_name'] = d['name']
        #t['slug'] = self.create_slug(t['info']['title'])
        t['category'] = d.get('category')
        for att in d['attachments']:
          if att['name'] == 'LOGO':
            t['art']['icon'] = API_IMAGES + att['value']
            t['art']['poster'] = t['art']['icon']
        t['info']['playcount'] = 1 # Set as watched
        t['subscribed'] = self.is_subscribed_channel(t['id'])
        t['source_type'] = d['sourceType']
        if t['source_type'] == 'IP':
          t['ip'] = d.get('ip')
          t['port'] = d.get('port')
        for f in d['extrafields']:
          if f['name'] == 'externalStreamingUrl':
            try:
              pars = json.loads(f['value'])
              if 'externalURL' in pars:
                t['playback_url'] = pars['externalURL']
              if 'provider_channel_params' in pars['params']['providerParams']:
                t['playback_url'] += '?' + pars['params']['providerParams']['provider_channel_params']
            except:
              pass
          elif f['name'] == 'channelDASContextParameters':
            try:
              pars = json.loads(f['value'])
              if 'bpkio_serviceid' in pars:
                t['bpkio_serviceid'] = pars['bpkio_serviceid']
            except:
              pass
          elif f['name'] == 'channelDAS':
              t['channelDAS'] = (f['value'] == 'true')
        res.append(t)
      return res

    def get_channels_list_with_epg(self):
      channels = self.get_channels_list()
      epg = self.get_epg()
      import time
      now = int(time.time() * 1000)
      self.add_epg_info(channels, epg, now)
      return channels

    def add_live_extra_info(self, program_id, t):
      url = endpoints['get-extended-program'].format(program_external_id=program_id)
      #LOG(url)
      data = self.load_json(url)
      data = data['response']
      if not 'title' in t['info']: t['info']['title'] = data['name']
      t['info']['plot'] = data['description']
      t['info']['year'] = data['year']
      t['info']['director'], t['info']['cast'] = self.get_contributors(data['contributors'])
      t['info']['country'] = self.get_country(data['countries'])
      t['info']['genre'] = self.get_genre(data['genreEntityList'])
      t['art'] = self.get_art(data['attachments'])
      if 'prName' in data: t['info']['mpaa'] = data['prName'].replace('ML_', '')

    def epg_to_movies(self, channel_id, date=None):
      epg = self.get_epg(date=date)
      videos = []
      if not channel_id in epg: return videos
      for p in epg[channel_id]:
        if sys.version_info[0] < 3:
          p['date_str'] = unicode(p['date_str'], 'utf-8')
        label = '[B]{}[/B] {}'.format(p['date_str'], p['name'])
        aired = (p['startDate'] <= (time.time() * 1000))
        t = {}
        t['program_title'] = p['name']
        t['info'] = {}
        t['info']['title'] = label
        t['type'] = 'movie'
        t['stream_type'] = 'tv'
        t['id'] = p['channel_id']
        t['info']['plot'] = p['description']
        t['info']['duration'] = (p['endDate'] - p['startDate']) / 1000
        t['info']['mediatype'] = 'movie'
        t['art'] = p.get('art')
        t['program_id'] = p['program_id']
        t['is_catchup'] = True
        t['info']['playcount'] = 1 # Set as watched
        t['info']['aired'] = date2str(p['startDate'], '%Y-%m-%d')
        t['subscribed'] = self.is_subscribed_channel(p['channel_id'])
        t['startDate'] = p['startDate']
        t['endDate'] = p['endDate']
        t['aired'] = aired
        t['info_id'] = t['program_id']
        t['series'] = p['series']
        if self.add_extra_info:
          self.add_video_extra_info(t)
        videos.append(t)
      return videos

    def check_video_in_ticket_list(self, id):
      url = endpoints['get-video-ticket-list']
      #LOG(url)
      data = self.load_json(url)
      #print_json(data)
      for t in data['response']:
        if t['videoExternalId'] == id:
          #print_json(t)
          return True
      return False

    def order_video(self, id):
      import uuid
      terminal_identifier = 'CHROME_' + str(uuid.uuid4()).upper()
      url = endpoints['order-video'].format(external_video_id=id, model_external_id=self.device['type'], terminal_identifier=terminal_identifier)
      data = self.load_json(url, check_errors=False)
      return data

    def get_video_playback_url(self, id):
      url = endpoints['get-video-playing-info'].format(video_external_id=id, model_external_id=self.device['type'], serial_number=self.device['id'])
      data = self.load_json(url)
      return data

    def get_recording_playback_url(self, id):
      url = endpoints['get-live-playing-info'].format(recording_id=id, serial_number=self.device['id'])
      data = self.load_json(url)
      return data

    def get_u7d_playback_url(self, id):
      data = self.get_video_info(id)
      #print_json(data)
      video_id = data['response'].get('id')

      program_id = '';
      for d in data['response']['metadata']:
        if d['name'] == 'ProgramID':
          program_id = d['value']
          break

      external_channel_id = data['response']['externalChannelId']
      content_provider = data['response']['contentProvider'];
      LOG('program_id: {} external_channel_id: {} content_provider: {}'.format(program_id, external_channel_id, content_provider))

      url = endpoints['get-u7d-playing-info'].format(channel_external_id=external_channel_id, program_external_id=program_id, serial_number=self.device['id'])
      data = self.load_json(url)
      data['video_id'] = video_id
      return data

    def get_tv_playback_url(self, id):
      url = endpoints['get-tv-playing-info'].format(channel_external_id=id, serial_number=self.device['id'])
      data = self.load_json(url)
      return data

    def get_tv_playback_url_start(self, id, program_external_id):
      url = endpoints['get-u7d-playing-info'].format(channel_external_id=id, program_external_id=program_external_id, serial_number=self.device['id'])
      data = self.load_json(url)
      return data

    def get_playback_url(self, id, stype, program_id = None):
      playback_url = None
      token = None
      source_type = ''
      video_id = None
      if stype == 'vod':
        data = self.get_video_playback_url(id)
        LOG('data: {}'.format(data))
        playback_url = data['response']['url']
        token = data['response']['token']
        license_url = data['response']['license_url']
        video_id = data['response']['id']
        LOG('license_url: {}'.format(license_url))
      else:
        if stype == 'rec':
          data = self.get_recording_playback_url(id)
          video_id = id
        elif stype == 'tv':
          if program_id:
            data = self.get_tv_playback_url_start(id, program_id)
          else:
            data = self.get_tv_playback_url(id)
        elif stype == 'u7d':
          data = self.get_u7d_playback_url(id)
          video_id = data.get('video_id')
        LOG('data: {}'.format(data))
        playback_url = data['response']['playingUrl']
        token = data['response']['casToken']
        source_type = data['response']['sourceType'];
      return {'playback_url': playback_url, 'token': token, 'source_type': source_type, 'video_id': video_id}

    def open_session(self, id):
      url = endpoints['open-session'].format(contentId=id, deviceId=self.device['id'], accountId=self.username)
      data = self.load_json(url)
      return data

    def mark_position_vod(self, video_id, video_external_id, position):
      url = endpoints['mark-position-vod'].format(video_id=video_id, video_external_id=video_external_id, position=position)
      LOG(url)
      data = self.load_json(url)
      return data

    def mark_position_recording(self, recording_id, position):
      url = endpoints['mark-position-recording'].format(recording_id=recording_id, position=position)
      LOG(url)
      data = self.load_json(url)
      return data

    def get_continue_watching(self):
      data = []
      for source in ['vod', 'personal-recording']:
        url = endpoints['get-viewing-positions'].format(offset=0, limit=50, view_source=source)
        data += self.load_json(url)
      #self.cache.save_file('continue.json', json.dumps(data, ensure_ascii=False))

      res = []
      for d in data:
        c = d['content']
        id = c['id']
        if d['viewSource'] == 'VOD':
          id = id.replace('_JIT', '') + '_PAGE_HD'
        t = {'type': 'movie', 'subscribed': True}
        t['info'] = {'mediatype': 'movie'}
        t['id'] = id
        t['info']['duration'] = c['duration']

        if d['viewSource'] == 'VOD' and c['type'] == 'Episode':
          t['info']['title'] = '{} {}x{} - {}'.format(c['seriesName'], c['seasonNumber'], c['episodeNumber'], c['name'])
          t['art'] = self.get_art(c['seriesImages'], 'path')
        else:
          t['info']['title'] = c['name']
          t['art'] = self.get_art(c['images'], 'path')

        if d['viewSource'] == 'PERSONAL_RECORDING':
          t['stream_type'] = 'rec'
        else:
          if 'U7D' in id:
            t['stream_type'] = 'u7d'
          else:
            t['stream_type'] = 'vod'

        t['stream_position'] = d['viewDuration']

        res.append(t)

      #return data
      return res

    def get_identity_cookie(self, text):
      identity = ''
      m = re.match(r'identity=(.*)', text)
      if m:
        identity = m.group(1)
      return identity

    def get_profiles(self):
      url = endpoints['get-profile-list']
      data = self.load_json(url)
      base_img_url = 'https://pc.orangetv.orange.es/pc/api/rtv/v1/images/attachments_new/profiles/Orange'
      res = []
      for i in data['response']:
        img_url = base_img_url
        if i['image'].startswith('/default'):
          img_url += '/defaultImages'
        p = {'name': i['name'], 'id': str(i['id']), 'image': img_url + i['image']}
        res.append(p)
      return res

    def change_profile(self, id):
      self.profile_id = id
      self.cache.save_file('profile_id.conf', self.profile_id)

    def login(self):
      # Load cookie from cache
      cookie = self.cache.load('cookie.conf', 1*60)
      if cookie:
        self.cookie = cookie
        return True

      if not self.username or not self.password:
        return False

      # Get new cookie
      headers = self.net.headers.copy()
      headers['Cookie'] =  self.cookie

      username = self.username
      if '@' in username: username = 'Orange.' + username
      url = endpoints['login-rtv'] + '&username=' + username
      data = {'username': username, 'password': decode_base64(self.password)}
      response = self.net.session.post(url, headers=headers, data=data)
      content = response.content.decode('utf-8')
      #LOG(content)
      data = json.loads(content)
      #print_json(data)
      if data['response']['status'] != 'SUCCESS':
        LOG(content)
        return False

      # Identity
      initial_cookie = 'timestamp=' + str(data['metadata']['timestamp']) +'; identity='+ self.get_identity_cookie(data['response']['message']) + '; '

      """
      #LOG(response.cookies)
      cjar = response.cookies
      d = cjar.get_dict()
      LOG(d)

      initial_cookie = 'timestamp=' + d['timestamp'] +'; identity=' + d['identity'] + '; '
      """

      LOG('initial_cookie: {}'.format(initial_cookie))

      url = endpoints['login-reco']
      headers['Cookie'] = initial_cookie
      data = self.net.load_data(url, headers)
      #print_json(data)
      if data['response']['status'] != 'SUCCESS':
        return False

      # Compass identity
      new_cookie = initial_cookie + 'compass-identity=' + self.get_identity_cookie(data['response']['message'])
      LOG('new_cookie: {}'.format(new_cookie))

      headers['Cookie'] = new_cookie

      # Profile
      if not self.profile_id:
        url = endpoints['get-profile-list']
        data = self.net.load_data(url, headers)
        #print_json(data)
        if len(data['response']) > 0:
          self.profile_id = str(data['response'][0]['id'])
          self.cache.save_file('profile_id.conf', self.profile_id)

      if self.profile_id:
        url = endpoints['login-reco'] + '&profile_id=' + self.profile_id
        data = self.net.load_data(url, headers)
        #print_json(data)
        if data['response']['status'] != 'SUCCESS':
          return False
        new_cookie = initial_cookie + 'compass-identity=' + self.get_identity_cookie(data['response']['message'])

      LOG('new cookie: {}'.format(new_cookie))
      self.cookie = new_cookie

      # Get missing part of the cookie from the channels response header
      if '/pc/' in url:
        #data = self.download_bouquet()
        #bouquet = data['response'][0]['id']
        #_, response_cookie = self.download_channels(bouquet)
        _, response_cookie = self.download_subscribed_channels()
        LOG('response_cookie: {}'.format(response_cookie))
        if response_cookie:
          self.cookie = response_cookie +'; '+ self.cookie

      self.cache.save_file('cookie.conf', self.cookie)
      return True

    def add_search(self, search_term):
      self.search_list.append(search_term)
      self.cache.save_file('searchs.json', json.dumps(self.search_list, ensure_ascii=False))

    def delete_search(self, search_term):
      self.search_list = [s for s in self.search_list if s != search_term]
      self.cache.save_file('searchs.json', json.dumps(self.search_list, ensure_ascii=False))

    def main_listing(self):
      l =    ({'name': 'AMC+', 'id': 'AMC_PLUS_10002'},
              {'name': 'AMC Selekt', 'id': 'AMC_10002'},
              {'name': 'Universal+', 'id': 'UNIV_10000'},
              #{'name': 'Canal Series', 'id': 'SED_15696'},
              {'name': 'AXN Now', 'id': 'SED_14876'},
              {'name': 'TNT Now', 'id': 'TNT_10002'},
              {'name': 'Foxnow', 'id': 'SED_15416'},
              {'name': 'Cosmo On', 'id': 'COSMON_10002'},
              {'name': 'National Geographic Now', 'id': 'SED_16713'},
              #{'name': 'Lionsgate+ Películas', 'id': 'SED_15338'},
              #{'name': 'Lionsgate+ Series', 'id': 'SED_15340'},
              #{'name': 'Movistar Series 2', 'id': 'SED_13040'},
              {'name': 'Películas', 'id': 'TVPLAY_14028'},
              {'name': 'Últimos 7 días', 'id': 'U7D%20TVPLAY'})
      res = []
      for i in l:
        res.append({'id': i['id'], 'info':{'title':i['name']}, 'type': 'category'})
      return res

    def get_rows(self, id):
      filename = 'cache/ROW_' + id + '.json'
      content = self.cache.load(filename)
      if content:
        return json.loads(content)

      subdata = self.get_subscription_info()
      headers = self.net.headers.copy()
      headers['Cookie'] =  self.cookie
      url = endpoints['get-rows']

      data = {
        'services': ','.join(self.entitlements),
        'tvpacks': subdata['tvpacks'],
        'bouquet_id': subdata['bouquet'],
        'channels': ','.join(self.subscribed_channels),
        'sp': subdata['offer'],
        'myTeam': 'NA',
        'available_sp': subdata['available_sp'],
        'from': 0,
        'count': 42,
        'external_id': id,
        'resolution': 'SD,HD',
        'device_type': 'PC',
        'profile_type': 'general',
        'profileId': self.profile_id,
        'version': 1,
      }
      #print_json(data)
      response = self.net.session.post(url, headers=headers, json=data)
      content = response.content.decode('utf-8')
      #Orange.save_file('/tmp/rows.json', content)
      data = json.loads(content)
      res = []
      for i in data['rows']:
        if 'title' in i and len(i['elements']) > 0:
          for e in i['elements']:
            if not 'actions' in e: continue
            #print_json(e)
            entry_point = e['actions'][0]['entryPoint']
            if e['type'] == 'seeAll' and ('browsing' in entry_point or 'getRows' in entry_point):
              #print(e)
              id = entry_point.rsplit('/', 1)[-1]
              t = {'info':{}, 'id':id}
              name = i['title']
              if 'buttonLabel' in e['actions'][0] and e['actions'][0]['buttonLabel'] != i['title']:
                name = name + ' - ' + e['actions'][0]['buttonLabel']
              elif 'name' in e and e['name'] != i['title']:
                name = name +' - ' + e['name']
              t['info']['title'] = name
              if 'browsing' in entry_point:
                t['type'] = 'category'
                res.append(t)
              elif 'getRows' in entry_point:
                t['type'] = 'row'
                res.append(t)
      self.cache.save_file(filename, json.dumps(res, ensure_ascii=False))
      return res

    def get_elements(self, external_id, row_id):
      filename = 'cache/ELEMENT_' + external_id + '_' + row_id + '.json'
      content = self.cache.load(filename)
      if content:
        return json.loads(content)

      subdata = self.get_subscription_info()
      headers = self.net.headers.copy()
      headers['Cookie'] =  self.cookie
      url = endpoints['get-elements']

      data = {
        'services': ','.join(self.entitlements),
        'tvpacks': subdata['tvpacks'],
        'bouquet_id': subdata['bouquet'],
        'channels': ','.join(self.subscribed_channels),
        'sp': subdata['offer'],
        'myTeam': 'NA',
        'available_sp': subdata['available_sp'],
        'from': 0,
        'count': 42,
        'external_id': external_id,
        'row_id': row_id,
        'resolution': 'SD,HD',
        'device_type': 'PC',
        'profile_type': 'general',
        'profileId': self.profile_id,
        'version': 1,
      }
      #print_json(data)
      response = self.net.session.post(url, headers=headers, json=data)
      content = response.content.decode('utf-8')
      #Orange.save_file('/tmp/elements.json', content)
      data = json.loads(content)
      res = []
      for i in data['elements']:
        if 'actionsOnEvents' in i:
          for e in i['actionsOnEvents']:
            if e['event'] == 'onClick':
              action = e['action']
              if action.startswith('/browsing'):
                res.append({'info':{'title': i['name']}, 'id': action.replace('/browsing/',''), 'type': 'category'})
      return res

    def get_vod_catalog(self, row_id='Home_Inicio_TVPLAY'):
      #res = self.get_rows('Home_Inicio_TVPLAY')
      res = self.get_elements('Home_Inicio', 'EDITORIAL_REVAMP_ROW_CHIPS')
      #res.append({'info':{'title': 'SkyShowtime - Películas'}, 'id': 'SKY_10016', 'type': 'category'})
      #res.append({'info':{'title': 'SkyShowtime - Series'}, 'id': 'SKY_10026', 'type': 'category'})
      res.append({'info':{'title': 'Películas'}, 'id': 'TVPLAY_14028', 'type': 'category'})
      return res

    def export_channels(self):
      if sys.version_info[0] >= 3:
        from urllib.parse import urlencode
      else:
        from urllib import urlencode

      channels = self.get_channels_list()
      res = []
      for c in channels:
        if not c['subscribed']: continue
        if c['source_type'] in ['IP', 'DVB-SI']: continue # Not supported
        t = {}
        t['name'] = c['channel_name']
        t['id'] = c['id']
        t['logo'] = c['art'].get('icon')
        t['preset'] = c['dial']
        t['stream'] = 'plugin://plugin.video.orange.spain/?action=play&id={}&stype=tv&source_type={}'.format(c['id'], c['source_type'])
        if 'playback_url' in c:
          t['stream'] += '&' + urlencode({'playback_url': c['playback_url']})
        res.append(t)
      return res

    def export_epg(self):
      res = {}
      epg = self.get_epg()
      channels = self.get_channels_list()
      for channel in channels:
        id = channel['id']
        if not channel['subscribed'] or not id in epg: continue
        res[id] = []
        for e in epg[id]:
          t = {}
          t['title'] = e['desc1']
          t['subtitle'] = e['desc2']
          t['start'] = datetime.utcfromtimestamp(e['startDate']/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
          t['stop'] = datetime.utcfromtimestamp(e['endDate']/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
          t['description'] = e['description']
          if 'art' in e:
            t['image'] = e['art']['poster']
          if 'genres' in e:
            t['genre'] = ', '.join(e['genres'])
          t['stream'] = 'plugin://plugin.video.orange.spain/?action=play&id={}&stype=tv&program_id={}'.format(id, e['program_id'])
          res[id].append(t)
      return res

    def export_channels_to_m3u8(self, filename):
      channels = self.export_channels()
      items = []
      for t in channels:
        item = '#EXTINF:-1 tvg-name="{name}" tvg-id="{id}" tvg-logo="{logo}" tvg-chno="{preset}" group-title="Orange TV" catchup="vod",{name}\n{stream}\n\n'.format(
            name=t['name'], id=t['id'], logo=t['logo'], preset=t['preset'], stream=t['stream'])
        items.append(item)
      res = '#EXTM3U\n## Orange TV\n{}'.format(''.join(items))
      with io.open(filename, 'w', encoding='utf-8', newline='') as handle:
        handle.write(res)

    def export_epg_to_xml(self, filename):
      if sys.version_info[0] < 3:
        # Python 2
        from cgi import escape as html_escape
      else:
        # Python 3
        from html import escape as html_escape

      channels = self.export_channels()
      res = []
      res.append('<?xml version="1.0" encoding="UTF-8"?>\n' + 
                 '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n' + 
                 '<tv>\n')

      for t in channels:
        res.append('<channel id="{}">\n'.format(t['id']) + 
                  '  <display-name>{}</display-name>\n'.format(t['name']) + 
                  '  <icon src="{}"/>\n'.format(t['logo']) + 
                  '</channel>\n')

      epg = self.export_epg()
      for ch in channels:
        if not ch['id'] in epg: continue
        for e in epg[ch['id']]:
          start = datetime.strptime(e['start'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H%M%S +0000")
          stop = datetime.strptime(e['stop'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d%H%M%S +0000")
          url = e.get('stream', None)
          if url:
            url = url.replace('&', '&amp;')
          res.append('<programme start="{}" stop="{}" channel="{}"'.format(start, stop, ch['id']) +
                    (' catchup-id="{}"'.format(url) if url else "") +
                    '>\n' +
                    '  <title>{}</title>\n'.format(html_escape(e['title'])) +
                    '  <sub-title>{}</sub-title>\n'.format(html_escape(e['subtitle'])))
          if 'image' in e:
            res.append('  <icon src="{}"/>\n'.format(e['image']))
          if 'description' in e:
            res.append('  <desc>{}</desc>\n'.format(html_escape(e['description'])))
          if 'genre' in e:
            res.append('  <category>{}</category>\n'.format(e['genre']))
          if 'credits' in e and len(e['credits']) > 0:
            res.append('  <credits>\n');
            for c in e['credits']:
              if c['type'] == 'director':
                res.append('    <director>{}</director>\n'.format(c['name']))
              elif c['type'] == 'actor':
                res.append('    <actor>{}</actor>\n'.format(c['name']))
            res.append('  </credits>\n');
          res.append('</programme>\n')
      res.append('</tv>\n')
      with io.open(filename, 'w', encoding='utf-8', newline='') as handle:
        handle.write(''.join(res))

    @staticmethod
    def save_file(filename, content):
      if sys.version_info[0] < 3:
        if not isinstance(content, unicode):
          content = unicode(content, 'utf-8')
      with io.open(filename, 'w', encoding='utf-8') as handle:
        handle.write(content)
