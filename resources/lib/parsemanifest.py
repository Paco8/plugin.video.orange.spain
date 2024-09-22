#!/usr/bin/env python
# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division

import re
import os
import requests
from .log import LOG

def download_split_subtitle(base_url, filename_template, start_number=0, sec_inc=2000):
  LOG('base_url: {}'.format(base_url))
  LOG('filename: {}'.format(filename_template))
  session = requests.Session()
  filename_template = filename_template.replace('$Time$', '{}')
  i = start_number
  res = []
  while True:
    if 'http' not in filename_template:
      url = os.path.join(base_url, filename_template.format(i))
    else:
      url = filename_template.format(i)

    LOG('Downloading {}'.format(url))
    response = session.get(url)
    if response.status_code != 200:
        break

    mdat_start = response.content.find(b'mdat')
    if mdat_start > -1:
       res.append(response.content[mdat_start+4:].decode('utf-8'))

    i += sec_inc
  return res


def extract_tracks(manifest):
  tracks = {'audios': [], 'subs': []}

  pattern = re.compile(r'<AdaptationSet.*?</AdaptationSet>', re.DOTALL)
  matches = re.findall(pattern, manifest)

  for track in matches:
    t = {}
    for label in ['contentType', 'Label', 'lang', 'mimeType', 'value', 'codecs', 'startNumber', 'media']:
      m = re.search(r'{}="(.*?)"'.format(label), track, re.DOTALL)
      t[label] = m.group(1) if m else ''

    m = re.search(r'<S t="(\d+)" d="(\d+)" r="(\d+)"/>', track, re.DOTALL)
    if m:
      t['start'] = int(m.group(1))
      t['sec_inc'] = int(m.group(2))
      t['chunks'] = int(m.group(3))

    m = re.search(r'Representation id="(.*?)"', track, re.DOTALL)
    if m:
      t['representation_id'] = m.group(1)
      t['filename'] = t['media'].replace('$RepresentationID$',t['representation_id'])

    if t['contentType'] in ['text', 'audio']:
      new_lang = re.sub(r'-[A-Z]{2}', '', t['lang'])
      if t['value'] == 'caption': new_lang += '-[CC]'
      if t['value'] == 'forced-subtitle': new_lang += '-[Forced]'
      t['new_lang'] = new_lang
    if t['contentType'] == 'text':
      tracks['subs'].append(t)
    elif t['contentType'] == 'audio':
      tracks['audios'].append(t)
  return tracks
