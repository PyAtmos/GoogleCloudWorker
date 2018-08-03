#FROM gcr.io/i-agility-205814/pyatmos
FROM gcr.io/i-agility-205814/pyatmos:20d31da190a2bbb66359da2a7bde591a2ee5e847
MAINTAINER Will Fawcett <willfaw@gmail.com>

RUN apt-get update \
  && apt-get install -y git \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

RUN mkdir -p /code/
RUN mkdir -p /results/
RUN cd /code/ && git clone https://gitlab.com/frontierdevelopmentlab/astrobiology/pyatmos.git
RUN cd /code/ && git clone https://gitlab.com/frontierdevelopmentlab/astrobiology/kuber-master.git

RUN cd /code/kuber-master  && pip3 install -r requirements.txt
RUN cd /code/pyatmos && pip3 install . 

##########

CMD sleep 35000d
