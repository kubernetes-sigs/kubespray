FROM centos:7.8.2003

RUN mkdir /kubespray

WORKDIR /kubespray

COPY . .

RUN yum update -y && \
    yum install -y openssl-devel python3-devel python3 python3-pi python3-pip rsync python3-libselinux gcc \
    https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm ca-certificates && \
    yum --enablerepo epel install -y moreutils curl gnupg2 sshpass && \
    curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.17.5/bin/linux/amd64/kubectl && \
    chmod a+x kubectl && cp kubectl /usr/local/bin/kubectl && \
    pip3 install -r requirements.txt && \
    yum remove docker docker-client docker-client-latest docker-common docker-latest \
    docker-latest-logrotate docker-logrotate docker-engine && \
    yum install -y yum-utils openssh-clients && \
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && \
    yum-config-manager --disable docker-ce-nightly && \
    yum install docker-ce docker-ce-cli containerd.io -y && \
    yum clean packages && yum clean headers && yum clean metadata && yum clean all

ENV LANG=C.UTF-8
