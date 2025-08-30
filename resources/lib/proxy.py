#!/usr/bin/env python
# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division

try:  # Python 3
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:  # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

try:  # Python 3
    from socketserver import TCPServer, ThreadingMixIn
except ImportError:  # Python 2
    from SocketServer import TCPServer, ThreadingMixIn

try:  # Python 3
    from urllib.parse import unquote, quote_plus
except ImportError:  # Python 2
    from urllib import unquote, quote_plus

try:  # Python 3
  from urllib.parse import parse_qsl
except:  # Python 2
  from urlparse import parse_qsl

import os
import requests
import threading
import socket
import re
import time
import sys
from contextlib import closing

from .b64 import encode_base64
from .addon import addon, profile_dir
from .mysession import MySession
from .log import LOG
from .useragent import useragent

from ttml2ssa import Ttml2SsaAddon
ttml = Ttml2SsaAddon()
ttml.ssa_timestamp_min_sep = 0

session = MySession()
session.headers.update({'user-agent': useragent})

import xbmc
kodi_version= int(xbmc.getInfoLabel('System.BuildVersion')[:2])

previous_tokens = []
manifest_base_url = ''
manifest_urls = {}
stype = ''
manifest_type = None
subtrack_ids = []

timeout = 2
ms_offset = 0

save_log = False
if save_log:
  import io
  fh = io.open(profile_dir + 'proxy.log', 'w', encoding='utf-8')

def SLOG(message):
  from datetime import datetime
  LOG(message)
  if save_log:
    now = datetime.now()
    strtime = now.strftime("%m/%d/%Y %H:%M:%S")
    fh.write(strtime +" ")
    if sys.version_info[0] > 2:
      fh.write(str(message))
    else:
      fh.write(message.decode('utf-8'))
    fh.write("\n")

def download_file(url, timeout=5):
  #SLOG('download_file: {}'.format(url))
  if timeout == 0: timeout = None
  retries = 0
  while retries < 5:
    url_t = url +'?_' + str(int(time.time()*1000)) if retries > 0 else url
    #SLOG('url_t: {}'.format(url_t))
    try:
      response = session.get(url_t, allow_redirects=True, timeout=timeout)
      if response.status_code == 200:
        content_size = len(response.content)
        content_length = int(response.headers.get("Content-Length", 0))
        SLOG('content_size: {} content_length: {}'.format(content_size, content_length))
        if content_length == 0 or content_size == content_length:
          return response.content, response.status_code
      else:
        SLOG('status_code: {}'.format(response.status_code))
    except Exception as e:
      SLOG('exception error: {}'.format(str(e)))
    retries += 1
    SLOG('WARNING: download failed. Retrying ({})'.format(retries))
    time.sleep(0.7)
  return response.content, 200


def download_subs(url, timeshift=0, timestamp_workaround=False):
    global ms_offset

    def download(url):
      data, _ = download_file(url, timeout=timeout)
      return data

    def next_offset(a):
      a += 1
      if a > 4: a = 0
      return a

    def add_text_to_box(subtext, binary=None):
      import struct

      if not binary:
        binary = b'\x00\x00\x00Tmoof\x00\x00\x00\x10mfhd\x00\x00\x00\x00\x00\x00\x01/\x00\x00\x00<traf\x00\x00\x00\x14tfhd\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00 trun\x00\x00\x07\x01\x00\x00\x00\x01\x00\x00\x00\\\x011-\x00\x00\x00\x04\x1d\x02\x80\x00@\x00\x00\x04%mdat'

      size = len(subtext)
      mdat_start = binary.find(b'mdat')

      if mdat_start > -1:
        new_bin = binary[0:mdat_start - 4]
        new_bin += struct.pack('>L', size+8)
        new_bin += b'mdat'
        new_bin += subtext

        trun_start = new_bin.find(b'trun')
        if trun_start > -1:
          flags = struct.unpack_from('>I', new_bin[trun_start:], 4)[0] & 0xffffff
          sample_count = struct.unpack_from('>I', new_bin[trun_start:], 8)[0]
          first_sample_flags_present = flags & 0x0004
          #LOG('{} {} {}'.format(hex(flags), sample_count, first_sample_flags_present))

          if sample_count > 0 and not first_sample_flags_present:
            sample_size = struct.unpack_from('>I', new_bin[trun_start:], 20)[0]
            #LOG('sample_size: {}'.format(sample_size))
            new_sample_size = len(subtext)
            new_bin = new_bin[:trun_start + 20] + struct.pack('>I', new_sample_size) + new_bin[trun_start + 20 + 4:]

        #LOG(repr(new_bin))
        return new_bin
      else:
        return binary

    content = download(url)
    lines = '<?xml version="1.0" encoding="utf-8"?><tt xml:lang="spa"><head></head><body><div>'

    subtext = b''
    sublines = ''
    binary = None

    if content:
      pos = content.find(b'<?xml')
      if pos > -1:
        binary = content[0:pos]
        subtext = content[pos:]
        SLOG('length: {}'.format(len(subtext)))
        LOG('timestamp_workaround: {}'.format(timestamp_workaround))
        #LOG(subtext)

        if subtext:
          ttml.shift = timeshift
          LOG('ttml.shift: {}'.format(ttml.shift))
          ttml.parse_ttml_from_string(subtext)
          for entry in ttml.entries:
            #LOG('ms_begin: {}'.format(entry['ms_begin']))
            ms_begin = entry['ms_begin']
            ms_end = entry['ms_end']
            if timestamp_workaround:
              ms_begin += ms_offset
              ms_end += next_offset(ms_offset)
            start = ttml._tc.ms_to_subrip(ms_begin).replace(',', '.')
            end = ttml._tc.ms_to_subrip(ms_end).replace(',', '.')
            text = entry['text'].replace('\n', '<br/>')
            if kodi_version < 21: sublines += '<div>'
            sublines += '<p begin="{}" end="{}">{}</p>'.format(start, end, text)
            if kodi_version < 21: sublines += '</div>'
            if timestamp_workaround:
              ms_offset = next_offset(ms_offset)

    lines += sublines
    lines += '</div></body></tt>'
    subtext = lines.encode('utf-8')
    #LOG(subtext)

    #LOG('manifest_type: {}'.format(manifest_type))
    #if manifest_type == 'ism': binary = None
    #if timestamp is not None: binary = None
    return add_text_to_box(subtext, binary)


def is_ascii(s):
  try:
    return s.isascii()
  except:
    return all(ord(c) < 128 for c in s)

def try_load_json(text):
  try:
    return json.loads(text)
  except:
    return None


class RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Handle http get requests, used for manifest"""
        path = self.path  # Path with parameters received from request e.g. "/manifest?id=234324"
        SLOG('==== HTTP GET Request received to {}'.format(path))
        try:
        #if True:
            if 'manifest' in path:
              global timeout
              timeout = addon.getSettingInt('proxy_timeout') / 1000
              LOG('proxy timeout: {}'.format(timeout))

              global stype, manifest_type, manifest_urls
              pos = path.find('?')
              path = path[pos+1:]
              params = dict(parse_qsl(path))
              LOG('params: {}'.format(params))
              orig_url = url = params['manifest']
              stype = params['stype']
              request_id = params['request_id']
              manifest_type = 'mpd' if '.mpd' in path else 'ism'
              LOG('url: {}'.format(url))
              LOG('stype: {}'.format(stype))
              LOG('manifest_type: {}'.format(manifest_type))

              #LOG(manifest_urls)
              if request_id in manifest_urls:
                url = manifest_urls[request_id]

              response = session.get(url, allow_redirects=True)
              LOG('headers: {}'.format(response.headers))
              baseurl = os.path.dirname(response.url)
              LOG('baseurl: {}'.format(baseurl))

              global manifest_base_url, subtrack_ids
              manifest_base_url = baseurl
              content = response.content.decode('utf-8')
              LOG('status_code: {}'.format(response.status_code))
              #LOG(content)

              if response.status_code == 200:
                manifest_urls[request_id] = response.url

              if manifest_type == 'ism':
                """ ISM manifest """
                if addon.getSettingBool('fix_languages'):
                  content = content.replace('Language="qaa"', 'Language="en"')
                  content = content.replace('Language="qha"', 'Language="es"')
                  content = re.sub(r'Language="q([^"]*)"', r'Language="es-[q\1]"', content)
                # Workaround for inputstream.adaptive bug #1064
                content = content.replace('IsLive="true"', 'IsLive="TRUE"')

                # Fix Neox subtitles
                if addon.getSettingBool('proxy_process_subs'):
                  content = content.replace('FourCC="DFXP"', 'FourCC="TTML"')

                # Find subtitles tracks
                matches = re.findall(r'<StreamIndex.*?Type="text".*?Url="(.*?)"', content)
                LOG('matches: {}'.format(matches))
                subtrack_ids = []
                for match in matches:
                  m = re.search(r'/Fragments\((.*?)=', match)
                  if m: subtrack_ids.append(m.group(0))
                LOG('subtrack_ids: {}'.format(subtrack_ids))
              elif manifest_type == 'mpd':
                """ MPD manifest """
                if addon.getSettingBool('fix_languages'):
                  content = content.replace('lang="qaa"', 'lang="en"')
                  content = content.replace('lang="qha"', 'lang="es"')
                  content = re.sub(r'lang="q([^"]*)"', r'lang="es-[q\1]"', content)

                # Find subtitles tracks
                matches = re.findall(r'<AdaptationSet[^>]*contentType="subtitle"[^>]*>.*?</AdaptationSet>', content, flags=re.DOTALL)
                LOG('matches: {}'.format(matches))
                subtrack_ids = []
                for match in matches:
                  m = re.search(r'/Fragments\((.*?)=', match)
                  if m: subtrack_ids.append(m.group(0))
                LOG('subtrack_ids: {}'.format(subtrack_ids))

              manifest_data = content
              self.send_response(200)
              self.send_header('Content-type', 'application/xml')
              self.end_headers()
              self.wfile.write(manifest_data.encode('utf-8'))
            elif 'QualityLevels' in path:
              url = manifest_base_url + path
              LOG('fragment url: {}'.format(url))

              is_sub = ('textstream' in url)
              if not is_sub:
                for sid in subtrack_ids:
                  if sid in url:
                    is_sub = True
                    break
              if 'Init' in path: is_sub = False
              LOG('is_sub: {}'.format(is_sub))
              #is_sub = False

              if is_sub and addon.getSettingBool('proxy_process_subs'):
                LOG('url: {}'.format(url))
                timeshift = 0
                timestamp_workaround = False
                if kodi_version < 21:
                  timestamp_workaround = True
                  if stype == 'vod':
                    m = re.search(r'Fragments\(.*?=(\d+)\)', url)
                    if m:
                      timestamp = int(m.group(1))
                      timeshift = (timestamp // 10000)
                      timestamp_workaround = False
                      LOG('timestamp: {} timeshift: {}'.format(timestamp, timeshift))
                content = download_subs(url, timeshift, timestamp_workaround)
                self.send_response(200)
                self.send_header('Content-type', 'video/mp4')
                self.end_headers()
                self.wfile.write(content)
                SLOG('==== HTTP GET End Request {}, length: {}'.format(path, len(content)))
                return
              if addon.getSettingBool('proxy_streams') and stype == 'vod':
                content, status_code = download_file(url, timeout=timeout)
                self.send_response(status_code)
                self.send_header('Content-type', 'video/mp4')
                self.end_headers()
                self.wfile.write(content)
                SLOG('==== HTTP GET End Request {}, length: {}'.format(path, len(content)))
                return
              # Redirect
              self.send_response(301)
              self.send_header('Location', url)
              self.end_headers()
              SLOG('==== HTTP GET End Request {}'.format(path))
            elif manifest_type == 'mpd':
              url = manifest_base_url + path
              #LOG('fragment url: {}'.format(url))
              result = None
              if addon.getSettingBool('proxy_process_subs'):
                # Live channels
                if 'subtitle' in url and 'init' not in url:
                  timeshift = 0
                  if kodi_version < 21:
                    m = re.search(r'stpp-(\d+).m4s', url)
                    if m:
                      timestamp = int(m.group(1))
                      LOG('timestamp: {}'.format(timestamp))
                      #timestamp = timestamp // 9 * 1000
                      #timeshift = -(timestamp // 10000)
                      timeshift = -(timestamp // 90)
                      LOG('timeshift: {}'.format(timeshift))
                  result = download_subs(url, timeshift, True)
                # Vod
                elif re.search(r'textstream_\w+=\d+-(\d+)', url):
                  result = download_subs(url, 0, False)

              if not result and addon.getSettingBool('proxy_streams') and not 'dashll' in url: # and stype == 'vod':
                #LOG('*** using proxy for {}'.format(url))
                result, status_code = download_file(url, timeout=timeout)

              if result:
                self.send_response(200)
                self.send_header('Content-type', 'video/mp4')
                self.end_headers()
                self.wfile.write(result)
              else:
                # Redirect
                self.send_response(301)
                self.send_header('Location', url)
                self.end_headers()
            else:
              self.send_response(404)
              self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            LOG('Exception error: {}'.format(str(e)))


    def do_POST(self):
        """Handle http post requests, used for license"""
        path = self.path  # Path with parameters received from request e.g. "/license?id=234324"
        print('HTTP POST Request received to {}'.format(path))
        if '/license' not in path:
            self.send_response(404)
            self.end_headers()
            return
        try:
        #if True:
            global previous_tokens
            pos = path.find('?')
            path = path[pos+1:]
            params = dict(parse_qsl(path))
            LOG('params: {}'.format(params))

            length = int(self.headers.get('content-length', 0))
            isa_data = self.rfile.read(length)
            LOG('isa_data length: {}'.format(length))
            LOG('isa_data: {}'.format(encode_base64(isa_data)))

            headers = {
              'Accept': '*/*',
              'Origin': 'https://orangetv.orange.es',
              'Referer': 'https://orangetv.orange.es/',
              'Sec-Fetch-Dest': 'empty',
              'Sec-Fetch-Mode': 'cors',
              'Sec-Fetch-Site': 'same-site',
            }

            token = params['token']
            LOG('token: {}'.format(token))
            LOG('previous_tokens: {}'.format(previous_tokens))
            if token in previous_tokens:
              LOG('duplicated token')
              from .orange import Orange
              o = Orange(profile_dir)
              program_id = None if params['program_id'] == 'None' else params['program_id']
              i = o.get_playback_url(params['id'], params['stype'], program_id)
              token = i['token']
              LOG('new token: {}'.format(token))
            previous_tokens.append(token)

            url = '{}?token={}'.format(params['lurl'], quote_plus(token))
            LOG('license url: {}'.format(url))
            response = session.post(url, data=isa_data, headers=headers)
            license_data = response.content

            LOG('license response length: {}'.format(len(license_data)))
            LOG('license response: {}'.format(encode_base64(license_data)))
            if is_ascii(license_data):
              LOG('license response (ascii): {}'.format(license_data))

            self.send_response(200)
            self.end_headers()
            self.wfile.write(license_data)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            LOG('Exception error: {}'.format(str(e)))


HOST = '127.0.0.1'
PORT = 57010

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class Proxy(object):
    started = False

    def check_port(self, port=0, default=False):
      try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
          s.bind((HOST, port))
          s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
          return s.getsockname()[1]
      except:
        return default

    def start(self):
        if self.started:
            return

        port = self.check_port(PORT)
        if not port:
          port = self.check_port(0)
        SLOG('port: {}'.format(port))

        self._server = ThreadedHTTPServer((HOST, port), RequestHandler)
        self._server.allow_reuse_address = True
        self._httpd_thread = threading.Thread(target=self._server.serve_forever)
        self._httpd_thread.start()
        self.proxyname = 'http://{}:{}'.format(HOST, port)
        addon.setSetting('proxy_address', self.proxyname)
        self.started = True
        LOG("Proxy Started: {}:{}".format(HOST, port))

    def stop(self):
        if not self.started:
            return

        self._server.shutdown()
        self._server.server_close()
        self._server.socket.close()
        self._httpd_thread.join()
        self.started = False
        SLOG("Proxy: Stopped")
        if save_log: fh.close()
