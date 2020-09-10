# Use imutable image tags rather than mutable tags (like ubuntu:18.04)
FROM ubuntu:bionic-20200807

ENV KUBE_VERSION=v1.19.2

RUN mkdir /kubespray
WORKDIR /kubespray
RUN apt update -y && \
    apt install -y \
    libssl-dev python3-dev sshpass apt-transport-https jq moreutils \
    ca-certificates curl gnupg2 software-properties-common python3-pip rsync
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
    add-apt-repository \
    "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable" \
    && apt update -y && apt-get install docker-ce -y
COPY . .
RUN /usr/bin/python3 -m pip install pip -U && /usr/bin/python3 -m pip install -r tests/requirements.txt && python3 -m pip install -r requirements.txt && update-alternatives --install /usr/bin/python python /usr/bin/python3 1

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$KUBE_VERSION/bin/linux/amd64/kubectl \
    && chmod a+x kubectl && cp kubectl /usr/local/bin/kubectl

# Some tools like yamllint need this
ENV LANG=C.UTF-8
