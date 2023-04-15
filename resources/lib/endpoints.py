# encoding: utf-8
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import unicode_literals, absolute_import, division

API_URL = 'https://pc.orangetv.orange.es/pc/api/'
API_RTV = API_URL + 'rtv/v1/'
API_RECO = API_URL + 'reco/v1/'
API_IMAGES = API_RTV + 'images'

endpoints = {'get-video': API_RTV + 'GetVideo?client=json&external_id={external_id}',
             'get-aggregated-video': API_RTV + 'GetAggregatedVideo?client=json&external_asset_id={external_asset_id}',
             'get-video-asset': API_RTV + 'GetVideoAsset?client=json&external_id={external_id}',
             'get-profile-wishlist': API_RECO + 'GetProfileWishList?client=json&device_models=PC',
             'get-extended-program-list': API_RTV + 'GetExtendedProgramList?client=json&filter_deleted=false&ext_program_channel_ids={ext_program_channel_ids}',
             'get-recording-ticket-list': API_RTV + 'GetRecordingTicketList?client=json',
             'get-tvshow-season-list': API_RTV + 'GetVideoTvShowSeasonList?client=json&series_external_id={series_external_id}',
             'get-tvshow-episode-list': API_RTV + 'GetVideoTvShowEpisodeList?client=json&season_external_id={season_external_id}',
             'get-video-ticket-list': API_RTV + 'GetVideoTicketList?client=json',
             'order-video': API_RTV + 'OrderVideo?client=json&external_video_id={external_video_id}&subscription=true&viewing_method=streaming&model_external_id={model_external_id}&terminal_identifier={terminal_identifier}',
             'get-terminal-list': API_RTV + 'GetTerminalList?client=json',
             'get-video-playing-info': API_RTV + 'GetVideoPlayingInfo?client=json&video_external_id={video_external_id}&model_external_id={model_external_id}&serial_number={serial_number}',
             'get-live-playing-info': API_RTV + 'GetLivePlayingInfo?client=json&include_cas_token=true&recording_id={recording_id}&time_shifting_service=npvr&serial_number={serial_number}',
             'get-u7d-playing-info': API_RTV + 'GetLivePlayingInfo?client=json&include_cas_token=true&time_shifting_service=catchup&channel_external_id={channel_external_id}&program_external_id={program_external_id}&serial_number={serial_number}',
             'get-tv-playing-info': API_RTV + 'GetLivePlayingInfo?client=json&include_cas_token=true&channel_external_id={channel_external_id}&serial_number={serial_number}',
             'get-profile-list': API_RECO + 'GetProfileList?client=json',
             'get-unified-list': API_RTV + 'GetUnifiedList?client=json&external_category_id={external_category_id}&statuses=published&definitions=SD;HD',
             'get-profile-channel-list': API_RECO + 'GetProfileChannelList?client=json',
             'get-bouquet-list': API_RTV + 'GetHouseholdBouquetList?client=json',
             'get-channel-list': API_RTV + 'GetChannelList?client=json&bouquet_id={bouquet_id}&model_external_id={model_external_id}&filter_unsupported_channels=true',
             'search-live': API_URL + 'search/v1/SearchLivePrograms?client=json&text={text}&max_results=100&image_name=all&fuzzy=true&device_models={device_models}&availability_type=all&order_by=broadcastStartTime',
             'search-vod': API_URL + 'search/v1/SearchVideos?services={services}&client=json&text={text}&content_type={content_type}&max_results=50&image_name=all&fuzzy=false&order_by=relevance&quality=sd,hd&search_by=title,genre',
             'order-recording': API_RTV + 'OrderRecording?client=json&program_id={program_id}&recursive=false&allow_scheduling_over_quota=false',
             'delete-recording': API_RTV + 'DeleteRecording?client=json&recording_id={recording_id}',
             'get-extended-program': API_RTV + 'GetExtendedProgram?client=json&program_external_id={program_external_id}',
             'register-terminal': API_RTV + 'RegisterTerminal?client=json&serial_number={serial_number}&name={name}&model_external_id={model_external_id}',
             'unregister-terminal': API_RTV + 'UnregisterTerminal?serial_number={serial_number}&client=json',
             'get-service-list': API_RTV + 'GetHouseholdServiceList?client=json',
             'get-subscribed-channels': API_RTV + 'GetHouseholdSubscribedChannelList?client=json',
             'open-session': 'https://sm.orangetv.orange.es/pc/api/sm/v1/openSession?type=live&contentId={contentId}&deviceId={deviceId}&accountId={accountId}',
             'login-rtv': API_RTV + 'Login?client=json',
             'login-reco': API_RECO + 'Login?client=json',
            }
