import logging
import pod2gen
from pydub import AudioSegment
import requests
import xml.etree.ElementTree as et


logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_boolean(s):
    if s == 'yes':
        return True
    else:
        return False


def parse_podcast_rss(rss_file):
    episode_ids = []

    podcast = pod2gen.Podcast()

    tree = et.parse(rss_file)
    root = tree.getroot()

    channel_node = root.find('channel')

    podcast.name = channel_node.find('title').text
    podcast.website = channel_node.find('link').text
    podcast.description = channel_node.find('description').text
    podcast.explicit = get_boolean(channel_node.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text)
    podcast.image = channel_node.find('{http://www.itunes.com/dtds/podcast-1.0.dtd}image').attrib['href']

    for episode_node in channel_node.findall('item'):
        episode = pod2gen.Episode()
        episode.title = episode_node.find('title').text
        episode.link = episode_node.find('link').text
        episode.summary = episode_node.find('description').text
        episode.publication_date = episode_node.find('pubDate').text
        episode_media_attrib = episode_node.find('enclosure').attrib
        episode.media = pod2gen.Media(episode_media_attrib['url'],
                                      episode_media_attrib['length'],
                                      episode_media_attrib['type'])
        podcast.add_episode(episode)
        episode_ids.append(episode.link.split('=')[-1])

    return podcast, set(episode_ids)


class PodcastGenerator:
    def __init__(self, youtube_client, s3_client, channel_id, s3_bucket, domain, fetch_all=False):
        self.youtube_client = youtube_client
        self.s3_client = s3_client
        self.channel_id = channel_id
        self.bucket = s3_bucket
        self.domain = domain
        self.fetch_all = fetch_all

        self.existing_audio_files = self.get_existing_audio_files_from_s3()

        try:
            self.s3_client.download_file(self.bucket, f'podcast/rss/{self.channel_id}.rss',
                                         f'/tmp/{self.channel_id}.rss')
            (self.podcast, self.episodes_id) = parse_podcast_rss(f'/tmp/{self.channel_id}.rss')
        except Exception as e:
            logger.warning(f'no podcast rss found for {self.channel_id}' + str(e))
            self.generate_new_podcast()
            self.episodes_id = set([])

    def generate_podcast_rss(self):
        self.generate_podcast()
        self.podcast.rss_file(f'/tmp/{self.channel_id}.rss')
        self.s3_client.upload_file(f'/tmp/{self.channel_id}.rss', self.bucket,
                                   f'podcast/rss/{self.channel_id}.rss')

    def generate_new_podcast(self):
        channel_detail = self.youtube_client.get_channel_detail(self.channel_id)
        self.podcast = pod2gen.Podcast()
        self.podcast.name = channel_detail.get('title')
        self.podcast.description = channel_detail.get('description')
        if self.podcast.description == '':
            self.podcast.description = self.podcast.name
        original_image_url = channel_detail.get('image')
        self.podcast.image = self.store_pic_to_s3(self.channel_id, original_image_url)
        self.podcast.website = channel_detail.get('link')
        self.podcast.copyright = channel_detail.get('copyright')
        self.podcast.explicit = False

    def generate_podcast(self):
        video_ids = self.youtube_client.get_channel_videos(self.channel_id, self.fetch_all)
        video_ids = [video_id for video_id in video_ids if video_id not in self.episodes_id]
        for video_detail in self.youtube_client.get_videos_detail(video_ids):
            episode = pod2gen.Episode()
            video_id = video_detail.get('video_id')
            episode.title = video_detail.get('title')
            episode.summary = video_detail.get('description')
            episode.publication_date = video_detail.get('pubDate')
            episode.link = video_detail.get('link')
            try:
                audio_stream = self.youtube_client.get_video_audio(video_id)
                audio_url = self.store_audio_to_s3(video_id, audio_stream)
            except Exception as e:
                logger.warning(f'fail to download video for {episode.link} ' + str(e))
                continue
            media = pod2gen.Media.create_from_server_response(audio_url)
            media.type = 'audio/mpeg'
            episode.media = media
            self.podcast.add_episode(episode)

    def store_pic_to_s3(self, _id, url):
        data = requests.get(url).content
        with open(f'/tmp/{_id}.jpg', 'wb') as f:
            f.write(data)
        self.s3_client.upload_file(f'/tmp/{_id}.jpg', self.bucket, f'podcast/pics/{_id}.jpg')
        return f'{self.domain}/podcast/pics/{_id}.jpg'

    def store_audio_to_s3(self, _id, audio_stream):
        key = f'podcast/audio/{self.channel_id}/{_id}.mp3'
        url = f'{self.domain}/{key}'
        if key in self.existing_audio_files:
            return url
        audio_stream.download('/tmp', f'{_id}')
        video_version = AudioSegment.from_file(f'/tmp/{_id}')
        video_version.export(f'/tmp/{_id}.mp3', format='mp3', bitrate='48k')
        self.s3_client.upload_file(f'/tmp/{_id}.mp3', self.bucket, key)
        logging.info(f'upload audio file to {key}.')
        return url

    def get_existing_audio_files_from_s3(self):
        key = f'podcast/audio/{self.channel_id}/'
        response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=key, MaxKeys=1000)
        return [] if 'Contents' not in response else [content['Key'] for content in response['Contents']]
