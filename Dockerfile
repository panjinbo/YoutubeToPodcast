FROM python:latest

RUN apt-get -y update
RUN apt-get install -y ffmpeg
# Install the function's dependencies using file requirements.txt
# from your project folder.
COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target .

# Copy function code
COPY config.json .
COPY main.py .
COPY podcast_generator/ ./podcast_generator
COPY youtube_client/ ./youtube_client

# Set the CMD to your handler
CMD python3 main.py