FROM python:2.7

RUN apt-get update && apt-get install -y --no-install-recommends \
    rsync
COPY . /opt/kubespray
RUN pip install -r /opt/kubespray/requirements.txt
RUN pip install docker-py==1.10.6

WORKDIR /opt/kubespray

