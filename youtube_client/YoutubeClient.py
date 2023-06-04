import datetime
import email.utils
import logging
import multiprocessing

import pytube
import requests

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def fetch_video_id_from_search_response(response):
    video_ids = []
    if 'items' in response:
        for video in response['items']:
            if 'id' in video and 'videoId' in video['id']:
                video_ids.append(video['id']['videoId'])
    return video_ids


def get_highest_resolution_image_link(options):
    option_order = ['maxres', 'standard', 'high', 'medium', 'default']
    for option in option_order:
        if options.get(option) is not None:
            return options.get(option).get('url')


class YoutubeClient:
    def __init__(self, api_key):
        self.api_key = api_key

    def get_channel_detail(self, channel_id):
        url = f'https://www.googleapis.com/youtube/v3/channels?key={self.api_key}&id={channel_id}&part=snippet'
        response = requests.get(url).json()
        snippet = response['items'][0]['snippet']
        title = snippet.get('title')
        description = snippet.get('description')
        image = get_highest_resolution_image_link(snippet.get('thumbnails'))
        copyright = snippet.get('customUrl')
        link = f'https://www.youtube.com/{copyright}'
        return {
            'title': title,
            'description': description,
            'image': image,
            'copyright': copyright,
            'link': link
        }

    def get_videos_detail(self, video_ids):
        pools = multiprocessing.Pool(20)
        return pools.map(self.get_video_detail, video_ids)

    def get_channel_videos(self, channel_id, fetch_all=False):
        video_ids = []
        max_page_result = 50 if fetch_all else 5
        url = f'https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channel_id={channel_id}&part=id&order' \
              f'=date&maxResults={max_page_result}'
        response = requests.get(url).json()
        video_ids.extend(fetch_video_id_from_search_response(response))
        if fetch_all is True and 'nextPageToken' in response:
            while 'nextPageToken' in response:
                next_page_token = response['nextPageToken']
                next_page_url = url + f'&pageToken={next_page_token}'
                response = requests.get(next_page_url).json()
                video_ids.extend(fetch_video_id_from_search_response(response))
        return video_ids

    def get_video_detail(self, video_id):
        url = f'https://www.googleapis.com/youtube/v3/videos?key={self.api_key}&part=snippet,player&id={video_id}'
        response = requests.get(url).json()
        snippet = response['items'][0]['snippet']
        title = snippet.get('title')
        description = snippet.get('description')
        image = get_highest_resolution_image_link(snippet.get('thumbnails'))
        link = f'https://www.youtube.com/watch?v={video_id}'
        pub_date = email.utils.format_datetime(
            datetime.datetime.strptime(snippet.get('publishedAt'), '%Y-%m-%dT%H:%M:%SZ'))
        return {
            'title': title,
            'description': description,
            'pubDate': pub_date,
            'image': image,
            'link': link,
            'video_id': video_id
        }

    def get_video_audio(self, video_id):
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        yt = pytube.YouTube(video_url)
        return yt.streams.filter(only_audio=True).first()
