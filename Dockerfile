FROM python:2.7.14-stretch

RUN mkdir /kubespray
WORKDIR /kubespray
RUN apt update -y && \
    apt install -y \
    libssl-dev python-dev sshpass apt-transport-https \
    ca-certificates curl gnupg2 software-properties-common
RUN curl -fsSL https://download.docker.com/linux/$(. /etc/os-release; echo "$ID")/gpg | apt-key add - && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/$(. /etc/os-release; echo "$ID") \
    $(lsb_release -cs) \
    stable" \
    && apt update -y && apt-get install docker-ce -y

COPY . .
RUN pip install -r tests/requirements.txt && pip install -r requirements.txt
