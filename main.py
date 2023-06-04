import boto3
import logging
import json

from podcast_generator.PodcastGenerator import PodcastGenerator
from youtube_client.YoutubeClient import YoutubeClient

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    logger.info('start running')

    # load config
    with open('config.json') as f:
        config = json.load(f)

    youtube_client = YoutubeClient(config['google_api_key'])

    s3_client = boto3.client('s3',
                             aws_access_key_id=config['aws_access_key'],
                             aws_secret_access_key=config['aws_secrete_key'])

    s3_bucket = config['s3_bucket']
    domain = config['domain']

    for channel in config.get('channels'):
        logger.info(f'start generating rss feed for {channel}')
        channel_id = channel.get('id')
        podcast_generator = PodcastGenerator(youtube_client, s3_client, channel_id, s3_bucket, domain,
                                             fetch_all=channel.get('fetch_all'))
        podcast_generator.generate_podcast_rss()

    logger.info('finish generating all channels rss feed')
