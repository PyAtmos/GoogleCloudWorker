##########
# slim dockerfile from
# https://hub.docker.com/r/fnndsc/ubuntu-python3/~/dockerfile/
FROM ubuntu:latest
RUN apt-get update \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip
ENTRYPOINT ["python3"]
##########

RUN pip install -r requirements.txt
RUN pip install ./pyatmos/
COPY ./worker.py /worker.py
COPY ./rediswq.py /rediswq.py
COPY ./utilities.py /utilities.py
COPY ./config.py /config.py

CMD  python worker.py