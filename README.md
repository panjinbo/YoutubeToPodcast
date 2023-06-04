# YouTube Video To Podcast 

I really like Apple Podcast this app on my phone. However, some of my favorite shows do not provide Podcast feed (most 
of them are video shows on YouTube -- and I prefer listening to those shows on my commute to work).

I could just open the YouTube app and listen to the show in background. But I hate switching between different apps, it 
would be better if I can just have one place to listen to all shows I follow.

Luckily Apple Podcast provides a feature to add custom RSS feed, so I wrote this small tool to:

1. Fetch videos in a Youtube channel.
2. Store the audio to AWS S3
3. Generate the Podcast RSS feed

![Youtube Show In Apple Podcast](https://media.panjinbo.com/github/youtub_to_podcast_podcast_app.png)


# How to use it

## Config file

In config.json, you need to provide:

1. Your Google API Key which is used to call YouTube API to get video details
2. Your AWS Access Key and Secrete Key which is used to store audio to AWS S3
3. S3 Bucket name in your AWS account where you want to store the audio
4. Domain is your CloudFront domain name if you enable the CDN for your S3 bucket or just
https://{YOUR_S3_BUCKET_NAME}.s3.{YOUR_S3_REGION}.amazonaws.com 
(You need to turn on the public access for your S3 bucket)
5. Channel Lists about what shows you want to generate podcast for. (To get channel id you could use this
[website](https://commentpicker.com/youtube-channel-id.php))

## Run it as native Python script

Install the dependencies of the scripts 
```
pip install -r requirements.txt
```

Run the main.py script

```
python main.py
```

## Run it in Container

Build the docker image

```
docker build -t youtube-to-podcast .
```

Run the docker

```
docker run youtube-to-podcast
```

## Podcast RSS Feed

The RSS feed will be in https://{DOMAIN}/podcast/rss/{CHANNEL_ID}.rss


# Deploy to AWS and Run it with a schedule

TO BE CONTINUED