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
from .log import LOG

from ttml2ssa import Ttml2SsaAddon
ttml = Ttml2SsaAddon()
ttml.ssa_timestamp_min_sep = 0

session = requests.Session()
session.headers.update({'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'})

previous_token = ''
manifest_base_url = ''
stype = ''
subtrack_ids = []

timeout = 2

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
        if content_size == content_length:
          return response.content, response.status_code
      else:
        SLOG('status_code: {}'.format(response.status_code))
    except Exception as e:
      SLOG('exception error: {}'.format(str(e)))
    retries += 1
    SLOG('WARNING: download failed. Retrying ({})'.format(retries))
    time.sleep(0.2)
  return response.content, 200

def download_subs(url):
    def download(url):
      data, _ = download_file(url, timeout=timeout)
      return data

    # Sometimes kodi skips one fragment. It seems that loading
    # two fragments at a time solves the problem.
    fragments = []
    m = re.search(r'Fragments\(.*?=(\d+)\)', url)
    if m:
      timestamp = int(m.group(1))
      seq = timestamp // 20000000
      LOG('timestamp: {} seq:{}'.format(timestamp, seq))
      next_timestamp = (seq+1) * 20000000
      LOG('next_timestamp: {}'.format(next_timestamp))
      new_url = url.replace('='+str(timestamp), '='+str(next_timestamp))
      LOG('new_url: {}'.format(new_url))
      if (seq % 2) == 0:
        fragments.append(download(url))
        fragments.append(download(new_url))
      else:
        content = ''
        SLOG('skipping {}'.format(timestamp))
    else:
      fragments.append(download(url))

    LOG('number of fragments: {}'.format(len(fragments)))

    lines = '<?xml version="1.0" encoding="utf-8"?><tt xml:lang="spa"><body><div>'
    for frag in range(0, len(fragments)):
      content = fragments[frag]
      if not content: break
      pos = content.find(b'<?xml')
      SLOG('frag: {}'.format(frag))
      if pos > -1:
        binary = content[0:pos]
        subtext = content[pos:]
        SLOG('frag: {} length: {}'.format(frag, len(subtext)))

        if subtext:
          ttml.shift = frag * 2000
          ttml.parse_ttml_from_string(subtext)
          for entry in ttml.entries:
            start = ttml._tc.ms_to_subrip(entry['ms_begin']).replace(',', '.')
            end = ttml._tc.ms_to_subrip(entry['ms_end']).replace(',', '.')
            text = entry['text'].replace('\n', '<br/>')
            lines += '<div><p begin="{}" end="{}">{}</p></div>\n'.format(start, end, text)

    lines += '</div></body></tt>'
    subtext = lines.encode('utf-8')

    size = len(subtext)

    binary = b'\x00\x00\x00Tmoof\x00\x00\x00\x10mfhd\x00\x00\x00\x00\x00\x00\x01/\x00\x00\x00<traf\x00\x00\x00\x14tfhd\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00 trun\x00\x00\x07\x01\x00\x00\x00\x01\x00\x00\x00\\\x011-\x00\x00\x00\x04\x1d\x02\x80\x00@\x00\x00\x04%mdat'

    import struct
    new_bin = binary[0:76]
    new_bin += struct.pack('>L', size)
    new_bin += binary[80:84]
    new_bin += struct.pack('>L', size+8)
    new_bin += binary[88:]

    #content = binary + subtext
    content = new_bin + subtext

    return content


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

              global stype
              pos = path.find('?')
              path = path[pos+1:]
              params = dict(parse_qsl(path))
              LOG('params: {}'.format(params))
              url = params['manifest']
              stype = params['stype']
              LOG('url: {}'.format(url))
              LOG('stype: {}'.format(stype))

              response = session.get(url, allow_redirects=True)
              LOG('headers: {}'.format(response.headers))
              baseurl = os.path.dirname(response.url)
              LOG('baseurl: {}'.format(baseurl))

              global manifest_base_url, subtrack_ids
              manifest_base_url = baseurl
              content = response.content.decode('utf-8')
              if addon.getSettingBool('fix_languages'):
                content = content.replace('Language="qaa"', 'Language="en"')
                content = content.replace('Language="qha"', 'Language="es"')
                content = re.sub(r'Language="q([^"]*)"', r'Language="es-[q\1]"', content)
              # Workaround for inputstream.adaptive bug #1064
              content = content.replace('IsLive="true"', 'IsLive="TRUE"')

              # Find subtitles tracks
              matches = re.findall(r'<StreamIndex Type="text".*?Url="(.*?)"', content)
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
              LOG('is_sub: {}'.format(is_sub))
              #is_sub = False

              if is_sub and addon.getSettingBool('use_ttml2ssa'):
                content = download_subs(url)
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
            else:
              self.send_response(404)
              self.end_headers()
        except Exception:
            self.send_response(500)
            self.end_headers()


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
            global previous_token
            pos = path.find('?')
            path = path[pos+1:]
            params = dict(parse_qsl(path))
            LOG('params: {}'.format(params))

            length = int(self.headers.get('content-length', 0))
            isa_data = self.rfile.read(length)
            LOG('isa_data length: {}'.format(length))
            LOG('isa_data: {}'.format(encode_base64(isa_data)))

            token = params['token']
            LOG('token: {}'.format(token))
            LOG('previous_token: {}'.format(previous_token))
            if previous_token == token:
              LOG('duplicated token')
              from .orange import Orange
              o = Orange(profile_dir)
              program_id = None if params['program_id'] == 'None' else params['program_id']
              _, token = o.get_playback_url(params['id'], params['stype'], program_id)
              LOG('new token: {}'.format(token))
            previous_token = token

            url = '{}?token={}'.format(params['lurl'], quote_plus(token))
            LOG('license url: {}'.format(url))
            response = session.post(url, data=isa_data)
            license_data = content= response.content
            LOG('license response length: {}'.format(len(license_data)))
            LOG('license response: {}'.format(encode_base64(license_data)))

            self.send_response(200)
            self.end_headers()
            self.wfile.write(license_data)
        except Exception:
            self.send_response(500)
            self.end_headers()


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
