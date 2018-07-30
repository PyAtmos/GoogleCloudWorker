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
COPY ./requirements.txt /home
COPY ./pyatmos /home/pyatmos
COPY ./worker.py /home
COPY ./rediswq.py /home
COPY ./utilities.py /home
COPY ./config.py /home
WORKDIR /home
RUN pip install -r requirements.txt
RUN pip install pyatmos/.
#CMD python worker.py
CMD ls -l /var/run/docker.sock
CMD id -nG
CMD docker run hello-world