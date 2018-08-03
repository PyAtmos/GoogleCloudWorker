#FROM gcr.io/i-agility-205814/pyatmos:c269dc45e448cd6f52d8bc1a2f05b04220b3346f
FROM gcr.io/i-agility-205814/pyatmos
MAINTAINER Will Fawcett <willfaw@gmail.com>

RUN apt-get update \
  && apt-get install -y vim \
  && apt-get install -y git \
  && apt-get install -y python3-pip python3-dev \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3 python \
  && pip3 install --upgrade pip

# Make sure we're in the top directory
RUN pwd && cd / && pwd
# Create directory structure 
RUN mkdir -p /code/
RUN mkdir -p /results/

# Trick to make sure the latest version of the git repos are always checked out
RUN /bin/true

# Checkout kuber-master and install packages
RUN cd /code/ && git clone https://gitlab.com/frontierdevelopmentlab/astrobiology/kuber-master.git
RUN cd /code/kuber-master  && pip3 install -r requirements.txt
RUN export WORKERDIR=/code/kuber-master

# Checkout pyatmos and install
RUN cd /code/ && git clone https://gitlab.com/frontierdevelopmentlab/astrobiology/pyatmos.git
RUN cd /code/pyatmos && pip3 install . 
RUN export PYATMOSDIR=/code/pyatmos

# Run the worker
CMD /code/kuber-master/run.sh 

# make sure the docker image persists 
#CMD sleep 35000d
