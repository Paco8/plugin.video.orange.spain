# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import sys
import json
import xbmc
import xbmcgui
import xbmcplugin
#import xbmcdrm

if sys.version_info[0] >= 3:
  import urllib.request as urllib2
  from urllib.parse import urlencode, parse_qsl, quote_plus
else:
  import urllib2
  from urllib import urlencode, quote_plus
  from urlparse import parse_qsl

import urllib
import base64
import re
import time

try:  # Kodi >= 19
  from xbmcvfs import translatePath
except ImportError:  # Kodi 18
  from xbmc import translatePath

import xbmcaddon
import os.path

from .log import LOG
from .orange import Orange
from .addon import *

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])


def get_url(**kwargs):
  return '{0}?{1}'.format(_url, urlencode(kwargs))


def play(params):
  id = params['id']
  stype = params['stype']
  LOG('**** play: id: {} stype: {}'.format(id, stype))

  try:
    if stype == 'vod':
      if not o.check_video_in_ticket_list(id):
        data = o.order_video(id)
        LOG('**** data: {}'.format(data))

    program_id = params['program_id'] if 'program_id' in params else None
    playback_url, token = o.get_playback_url(id, stype, program_id)

    manifest_type = 'ism'
    if 'source_type' in params:
      if   params['source_type'] == 'MPEGDash': manifest_type = 'mpd'
      elif params['source_type'] == 'HLS':      manifest_type = 'hls'
    LOG('manifest_type: {}'.format(manifest_type))

    proxy = o.cache.load_file('proxy.conf')
    #if stype == 'tv' and manifest_type == 'ism' and addon.getSettingBool('manifest_modification') and proxy:
    if manifest_type == 'ism' and addon.getSettingBool('manifest_modification') and proxy:
      playback_url = '{}/?manifest={}&stype={}'.format(proxy, quote_plus(playback_url), stype)

    #if stype == 'tv':
    #  response = o.session.get(playback_url)
    #  playback_url = response.url

    LOG('**** url: {} token: {}'.format(playback_url, token))

  except Exception as e:
    dialog = xbmcgui.Dialog()
    dialog.notification(addon.getLocalizedString(30200), str(e), xbmcgui.NOTIFICATION_ERROR, 5000) # Error
    return

  # https://cps.purpledrm.com/wv_certificate/cert_license_widevine_com.bin
  certificate = (
     'CsECCAMSEBcFuRfMEgSGiwYzOi93KowYgrSCkgUijgIwggEKAoIBAQCZ7Vs7Mn2rXiTvw7YqlbWY'
     'UgrVvMs3UD4GRbgU2Ha430BRBEGtjOOtsRu4jE5yWl5KngeVKR1YWEAjp+GvDjipEnk5MAhhC28V'
     'jIeMfiG/+/7qd+EBnh5XgeikX0YmPRTmDoBYqGB63OBPrIRXsTeo1nzN6zNwXZg6IftO7L1KEMpH'
     'SQykfqpdQ4IY3brxyt4zkvE9b/tkQv0x4b9AsMYE0cS6TJUgpL+X7r1gkpr87vVbuvVk4tDnbNfF'
     'XHOggrmWEguDWe3OJHBwgmgNb2fG2CxKxfMTRJCnTuw3r0svAQxZ6ChD4lgvC2ufXbD8Xm7fZPvT'
     'CLRxG88SUAGcn1oJAgMBAAE6FGxpY2Vuc2Uud2lkZXZpbmUuY29tEoADrjRzFLWoNSl/JxOI+3u4'
     'y1J30kmCPN3R2jC5MzlRHrPMveoEuUS5J8EhNG79verJ1BORfm7BdqEEOEYKUDvBlSubpOTOD8S/'
     'wgqYCKqvS/zRnB3PzfV0zKwo0bQQQWz53ogEMBy9szTK/NDUCXhCOmQuVGE98K/PlspKkknYVeQr'
     'OnA+8XZ/apvTbWv4K+drvwy6T95Z0qvMdv62Qke4XEMfvKUiZrYZ/DaXlUP8qcu9u/r6DhpV51Wj'
     'x7zmVflkb1gquc9wqgi5efhn9joLK3/bNixbxOzVVdhbyqnFk8ODyFfUnaq3fkC3hR3f0kmYgI41'
     'sljnXXjqwMoW9wRzBMINk+3k6P8cbxfmJD4/Paj8FwmHDsRfuoI6Jj8M76H3CTsZCZKDJjM3BQQ6'
     'Kb2m+bQ0LMjfVDyxoRgvfF//M/EEkPrKWyU2C3YBXpxaBquO4C8A0ujVmGEEqsxN1HX9lu6c5OMm'
     '8huDxwWFd7OHMs3avGpr7RP7DUnTikXrh6X0')

  token = quote_plus(token)

  import inputstreamhelper
  is_helper = inputstreamhelper.Helper(manifest_type, drm='com.widevine.alpha')
  if not is_helper.check_inputstream():
    xbmcgui.Dialog().notification(addon.getLocalizedString(30200), addon.getLocalizedString(30202), xbmcgui.NOTIFICATION_ERROR, 5000)
    return

  play_item = xbmcgui.ListItem(path= playback_url)
  if format(addon.getSetting('drm_type')) == 'Playready':
    license_url = o.get_license_url()
    license_options = ''
    play_item.setProperty('inputstream.adaptive.license_type', 'com.microsoft.playready')
  else:
    license_url = 'https://pc.orangetv.orange.es/pc/api/rtv/v1/widevinedrm'
    license_options = '||R{SSM}|'
    play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
  if addon.getSettingBool('use_proxy_for_license') and proxy:
    license_url = '{}/license?id={}&stype={}&program_id={}&token={}&lurl={}{}'.format(proxy, id, stype, program_id, token, license_url, license_options)
    play_item.setProperty('inputstream.adaptive.license_key', license_url)
  else:
    play_item.setProperty('inputstream.adaptive.license_key', '{}?token={}{}'.format(license_url, token, license_options))
  play_item.setProperty('inputstream.adaptive.server_certificate', certificate);
  play_item.setProperty('inputstream.adaptive.manifest_type', manifest_type)
  play_item.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0')

  if stype == 'tv' and program_id:
    play_item.setProperty('inputstream.adaptive.play_timeshift_buffer', 'true')

  if sys.version_info[0] < 3:
    play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
  else:
    play_item.setProperty('inputstream', 'inputstream.adaptive')

  if manifest_type == 'mpd':
    play_item.setMimeType('application/dash+xml')
  elif manifest_type == 'hls':
    play_item.setMimeType('application/x-mpegURL')
  else:
    play_item.setMimeType('application/vnd.ms-sstr+xml')

  # Add external subtitles
  if stype != 'tv' and 'slug' in params:
    slug = params['slug']
    if 'season' in params:
      season = int(params['season'])
      episode = int(params['episode'])
      subfolder = '{}/t{}/'.format(slug, season)
      subfilter = '.*((s|S){season:02d}(e|E){episode:02d}|{season:01d}x{episode:02d}).*\.(srt|ssa)'.format(season=season, episode=episode)
    else:
      subfolder = ''
      subfilter = '{}.*\.(srt|ssa)'.format(slug)

    LOG('**** subfolder: {} subfilter: {}'.format(subfolder, subfilter))
    subfiles = []
    subfolder = '{}orange/{}'.format(translatePath('special://subtitles'), subfolder)
    LOG('subfolder: {}'.format(subfolder))
    if sys.version_info[0] > 2:
      subfolder = bytes(subfolder, 'utf-8')
      subfilter = bytes(subfilter, 'utf-8')
    if os.path.exists(subfolder):
      for file in os.listdir(subfolder):
        if re.search(subfilter, file):
          subfiles.append(subfolder + file)
    LOG('**** subs: {}'.format(subfiles))
    play_item.setSubtitles(subfiles)

  play_item.setContentLookup(False)
  xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def input_window(heading, text = '', hidden = False):
  res = None
  keyboard = xbmc.Keyboard(text)
  keyboard.setHeading(heading)
  keyboard.setHiddenInput(hidden)
  keyboard.doModal()
  if (keyboard.isConfirmed()):
    res = keyboard.getText()
  del keyboard
  return res

def add_videos(category, ctype, videos):
  #LOG("*** TEST category: {} ctype: {}".format(category.encode('utf-8'), ctype))
  xbmcplugin.setPluginCategory(_handle, category)
  xbmcplugin.setContent(_handle, ctype)

  if ctype == 'movies' or ctype == 'seasons':
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL,
                    xbmcplugin.SORT_METHOD_VIDEO_YEAR, xbmcplugin.SORT_METHOD_DATEADDED,
                    xbmcplugin.SORT_METHOD_PLAYCOUNT, xbmcplugin.SORT_METHOD_LASTPLAYED]
    for sort_method in sort_methods:
      xbmcplugin.addSortMethod(_handle, sort_method)
  if ctype == 'episodes':
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_EPISODE)

  for t in videos:
    #LOG("*** TEST t: {}".format(t))
    if 'subscribed' in t:
      if addon.getSettingBool('only_subscribed') and t['subscribed'] == False: continue
      t['info']['title'] = o.colorize_title(t)
    title_name = t['info']['title'].encode('utf-8')
    if t['type'] == 'movie':
      list_item = xbmcgui.ListItem(label = title_name)
      list_item.setProperty('IsPlayable', 'true')
      list_item.setInfo('video', t['info'])

      if t['info']['mediatype'] == 'episode':
        list_item.setArt({'thumb': t['art']['thumb']})
      else:
        list_item.setArt(t['art'])

      url = get_url(action='play', id=t['id'], stype=t['stream_type'])
      if 'source_type' in t:
        url += '&source_type=' + t['source_type']
      if 'slug' in t:
        url += '&slug=' + t['slug']
      if 'season' in t['info']:
        url += '&season=' + str(t['info']['season'])
      if 'episode' in t['info']:
        url += '&episode=' + str(t['info']['episode'])

      if t['stream_type'] == 'tv' and 'program_id' in t:
        play_from_beginning_action = (addon.getLocalizedString(30170), "RunPlugin(" + url +'&menu=1&program_id=' +  t['program_id'] + ")")
        record_program_action = (addon.getLocalizedString(30171), "RunPlugin(" + get_url(action='add_recording', id=t['program_id']) + ")")
        if t.get('is_catchup', False):
          url += '&program_id=' + t['program_id']
          list_item.addContextMenuItems([record_program_action])
        else:
          list_item.addContextMenuItems([play_from_beginning_action, record_program_action])

      if t['stream_type'] == 'rec':
          action = get_url(action='delete_recording', id=t['id'], name=t['info']['title'].encode('utf-8'))
          list_item.addContextMenuItems([(addon.getLocalizedString(30173), "RunPlugin(" + action + ")")])

      xbmcplugin.addDirectoryItem(_handle, url, list_item, False)
    elif t['type'] == 'series':
      list_item = xbmcgui.ListItem(label = title_name)
      list_item.setInfo('video', t['info'])
      list_item.setArt(t['art'])
      xbmcplugin.addDirectoryItem(_handle, get_url(action='series', id=t['id'], name=title_name), list_item, True)
    elif t['type'] == 'season':
      list_item = xbmcgui.ListItem(label = title_name)
      list_item.setInfo('video', t['info'])
      list_item.setArt(t['art'])
      xbmcplugin.addDirectoryItem(_handle, get_url(action='season', id=t['id'], name=title_name), list_item, True)
    elif t['type'] == 'category':
      list_item = xbmcgui.ListItem(label = title_name)
      #list_item.setInfo('video', t['info'])
      #list_item.setArt(t['art'])
      xbmcplugin.addDirectoryItem(_handle, get_url(action='category', id=t['id'], name=title_name), list_item, True)

  xbmcplugin.endOfDirectory(_handle)

def open_folder(name, content_type = 'files'):
  xbmcplugin.setPluginCategory(_handle, name)
  xbmcplugin.setContent(_handle, content_type)

def close_folder(updateListing=False, cacheToDisc=True):
  xbmcplugin.endOfDirectory(_handle, updateListing=updateListing, cacheToDisc=cacheToDisc)

def add_menu_option(title, url, context_menu = None, info = None, art = None):
  list_item = xbmcgui.ListItem(label=title)
  list_item.setInfo('video', info)
  list_item.setArt(art)
  if context_menu:
    list_item.addContextMenuItems(context_menu)
  xbmcplugin.addDirectoryItem(_handle, url, list_item, True)

def list_vod():
  open_folder(addon.getLocalizedString(30111)) # VOD
  listing = o.main_listing()
  for l in listing:
    name = l['name'].encode('utf-8')
    add_menu_option(name, get_url(action='category', name=name, id=l['id']))
  close_folder()

def list_epg(params):
  LOG('list_epg: {}'.format(params))
  if 'id' in params:
    add_videos(params['name'], 'movies', o.epg_to_movies(params['id']))
  else:
    channels = o.get_channels_list()
    open_folder(addon.getLocalizedString(30107)) # EPG
    for t in channels:
      if addon.getSettingBool('only_subscribed') and t['subscribed'] == False: continue
      name = t['info']['title']
      add_menu_option(name, get_url(action='epg', id=t['id'], name=name.encode('utf-8')), art=t['art'])
    close_folder()

def list_devices(params):
  LOG('list_devices: params: {}'.format(params))

  devices = o.get_devices()

  if 'id' in params:
    if params['name'] == 'select':
      LOG('Selecting device {}'.format(params['id']))
      o.change_device(params['id'])
    elif params['name'] == 'delete':
      LOG('Deletin device {}'.format(params['id']))
      o.unregister_device(params['id'])
    elif params['name'] == 'create':
      LOG('Creating new device')
      name = input_window(addon.getLocalizedString(30154)) # Device name
      if name:
        try:
          o.register_device(name=name)
        except Exception as e:
          xbmcgui.Dialog().notification(addon.getLocalizedString(30200), str(e), xbmcgui.NOTIFICATION_ERROR, 5000) # Error

    xbmc.executebuiltin("Container.Refresh")
    return

  open_folder(addon.getLocalizedString(30108)) # Devices

  for d in devices:
    resolution = 'HD' if d['type'] in o.hd_devices else 'SD'
    name = '{} - [COLOR yellow]{}[/COLOR] [{}] ({})'.format(d['name'], resolution, d['type'],  d['reg_date'])
    if d['serial_number'] == o.device['id']:
      name = '[B][COLOR blue]' + name + '[/COLOR][/B]'

    select_action = get_url(action='devices', id=d['serial_number'], name='select')
    remove_action = get_url(action='devices', id=d['serial_number'], name='delete')
    cm = [(addon.getLocalizedString(30152), "RunPlugin(" + select_action + ")"),
          (addon.getLocalizedString(30151), "RunPlugin(" + remove_action + ")")]
    add_menu_option(name, select_action, cm)

  if len(devices) < 5:
    add_menu_option(addon.getLocalizedString(30153), get_url(action='devices', name='create', id='0')) # Add new

  close_folder(cacheToDisc=False)

def list_users(params):
  LOG('list_users: {}'.format(params))

  def ask_credentials(username=''):
    username = input_window(addon.getLocalizedString(30163), username) # Username
    if username:
      password = input_window(addon.getLocalizedString(30164), hidden=True) # Password
      if password:
        return username, password
    return None, None

  if 'name' in params and params['name'] == 'new':
    username, password = ask_credentials()
    if username:
      o.add_user(username, password)
      o.change_user(username)
    xbmc.executebuiltin("Container.Refresh")
  elif 'id' in params:
    if params['name'] == 'select':
      o.change_user(params['id'])
    elif params['name'] == 'delete':
      o.remove_user(params['id'])
    elif params['name'] == 'edit':
      username, password = ask_credentials(params['id'])
      if username:
        o.remove_user(params['id'])
        o.add_user(username, password)
        o.change_user(username)
    xbmc.executebuiltin("Container.Refresh")
  else:
    open_folder(addon.getLocalizedString(30160)) # Change user

    for u in o.users:
      name = u['username']
      if u['username'] == o.username: name = '[COLOR blue]' + name + '[/COLOR]'

      select_action = get_url(action='user', id=u['username'], name='select')
      remove_action = get_url(action='user', id=u['username'], name='delete')
      edit_action = get_url(action='user', id=u['username'], name='edit')
      cm = [(addon.getLocalizedString(30165), "RunPlugin(" + select_action + ")"),
            (addon.getLocalizedString(30167), "RunPlugin(" + edit_action + ")"),
            (addon.getLocalizedString(30162), "RunPlugin(" + remove_action + ")")]
      add_menu_option(name, select_action, cm)

    add_menu_option(addon.getLocalizedString(30161), get_url(action='user', name='new')) # Add new
    close_folder(cacheToDisc=False)

def search(params):
  search_term = params.get('search_term', None)
  if search_term:
    if params.get('name', None) == 'delete':
      o.delete_search(search_term)
      xbmc.executebuiltin("Container.Refresh")
    else:
      videos = o.search_vod(search_term, 'movie') + o.search_vod(search_term, 'series') + o.search_live(search_term)
      add_videos(addon.getLocalizedString(30117), 'movies', videos)
    return

  if params.get('name', None) == 'new':
    search_term = input_window(addon.getLocalizedString(30116)) # Search term
    if search_term:
      o.add_search(search_term)
    xbmc.executebuiltin("Container.Refresh")
    return

  open_folder(addon.getLocalizedString(30113)) # Search
  add_menu_option(addon.getLocalizedString(30113), get_url(action='search', name='new')) # New search

  for i in o.search_list:
    remove_action = get_url(action='search', search_term=i, name='delete')
    cm = [(addon.getLocalizedString(30114), "RunPlugin(" + remove_action + ")")]
    add_menu_option(i.encode('utf-8'), get_url(action='search', search_term=i), cm)

  close_folder(cacheToDisc=False)

def order_recording(program_id):
  try:
    data = o.order_recording(program_id)
    if data['response']['status'] == 'SUCCESS':
      xbmcgui.Dialog().notification(addon.getLocalizedString(30201), addon.getLocalizedString(30172), xbmcgui.NOTIFICATION_INFO, 5000)
  except Exception as e:
    xbmcgui.Dialog().notification(addon.getLocalizedString(30200), str(e), xbmcgui.NOTIFICATION_ERROR, 5000) # Error

def delete_recording(id, name):
  if sys.version_info[0] < 3:
    name = name.decode('utf-8')
  res = xbmcgui.Dialog().yesno(addon.getLocalizedString(30173), addon.getLocalizedString(30174).format(name))
  if res == True:
    o.delete_recording(id)
    xbmc.executebuiltin("Container.Refresh")

def router(paramstring):
  """
  Router function that calls other functions
  depending on the provided paramstring
  :param paramstring: URL encoded plugin paramstring
  :type paramstring: str
  """

  params = dict(parse_qsl(paramstring))
  if params:
    if params['action'] == 'play':
      LOG('play: {}'.format(paramstring))
      if 'menu=1' in paramstring:
        url = _url + '?' + paramstring.replace('&menu=1', '')
        xbmc.Player().play(url)
      else:
        play(params)
    elif params['action'] == 'wishlist':
      # Wishlist
      if not 'type' in params:
        open_folder(addon.getLocalizedString(30102)) # Wishlist
        add_menu_option(addon.getLocalizedString(30105), get_url(action='wishlist', type='movie')) # Movies
        add_menu_option(addon.getLocalizedString(30106), get_url(action='wishlist', type='series')) # Series
        close_folder()
      else:
        wl = o.get_wishlist()
        l = []
        for t in wl:
          if t['type'] == params['type']: l.append(t)
        ctype = 'tvshows' if params['type'] == 'series' else 'movies'
        add_videos(addon.getLocalizedString(30102), ctype, l) # Wishlist
    elif params['action'] == 'recordings':
      # Recordings
      add_videos(addon.getLocalizedString(30103), 'movies', o.get_recordings()) # Recordings
    elif params['action'] == 'series':
      add_videos(params['name'], 'seasons', o.get_seasons(params['id']))
    elif params['action'] == 'season':
      add_videos(params['name'], 'episodes', o.get_episodes(params['id']))
    elif params['action'] == 'category':
      add_videos(params['name'], 'movies', o.get_category_list(params['id']))
    elif params['action'] == 'tv':
      add_videos(addon.getLocalizedString(30104), 'movies', o.get_channels_list_with_epg())
    elif params['action'] == 'vod':
      list_vod()
    elif params['action'] == 'user':
      list_users(params)
    elif params['action'] == 'devices':
      list_devices(params)
    elif params['action'] == 'search':
      search(params)
    elif params['action'] == 'add_recording':
      order_recording(params['id'])
    elif params['action'] == 'epg':
      list_epg(params)
    elif params['action'] == 'delete_recording':
      delete_recording(params['id'], params['name'])
    else:
      raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
  else:
    # Main
    open_folder(addon.getLocalizedString(30101)) # Menu

    if not o.logged:
      xbmcgui.Dialog().notification(addon.getLocalizedString(30200), addon.getLocalizedString(30166), xbmcgui.NOTIFICATION_ERROR, 5000) # Login failed

    if o.logged:
      add_menu_option(addon.getLocalizedString(30104), get_url(action='tv')) # TV
      add_menu_option(addon.getLocalizedString(30107), get_url(action='epg')) # EGP
      add_menu_option(addon.getLocalizedString(30102), get_url(action='wishlist')) # My list
      add_menu_option(addon.getLocalizedString(30103), get_url(action='recordings')) # Recordings
      add_menu_option(addon.getLocalizedString(30111), get_url(action='vod')) # VOD
      add_menu_option(addon.getLocalizedString(30112), get_url(action='search')) # Search
      add_menu_option(addon.getLocalizedString(30108), get_url(action='devices')) # Devices

    # Accounts
    add_menu_option(addon.getLocalizedString(30160), get_url(action='user')) # Accounts
    close_folder()


def run():
  LOG('**** drm_type: {}'.format(addon.getSetting('drm_type')))

  global o
  o = Orange(profile_dir)
  #o.login()

  # Call the router function and pass the plugin call parameters to it.
  # We use string slicing to trim the leading '?' from the plugin call paramstring
  router(sys.argv[2][1:])
