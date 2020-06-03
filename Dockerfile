FROM centos:7.8.2003

RUN mkdir /kubespray
WORKDIR /kubespray
COPY . .
RUN yum update -y && \
    yum install -y openssl-devel python3-devel \
    python3 python3-pi python3-pip rsync python3-libselinux\
    https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm ca-certificates && \
    yum --enablerepo epel install -y moreutils curl gnupg2 sshpass && \
    yum install -y gcc python3-pip python3-devel openssl-devel python3-libselinux && \
    pip3 install -r requirements.txt && \
    curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.17.5/bin/linux/amd64/kubectl \
        && chmod a+x kubectl && cp kubectl /usr/local/bin/kubectl && \
        yum --enablerepo=epel -y install sshpass && yum remove docker docker-client docker-client-latest docker-common docker-latest \
    docker-latest-logrotate docker-logrotate docker-engine && yum install -y yum-utils && \
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo && \
    yum-config-manager --disable docker-ce-nightly && \
    yum install docker-ce docker-ce-cli containerd.io -y

#RUN apt update -y && \
#    apt install -y \
#    libssl-dev python3-dev sshpass apt-transport-https jq moreutils \
#    ca-certificates curl gnupg2 software-properties-common python3-pip rsync
#RUN  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - && \
#     add-apt-repository \
#     "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
#     $(lsb_release -cs) \
#     stable" \
#     && apt update -y && apt-get install docker-ce -y
#
#RUN pip3 install -r requirements.txt && update-alternatives --install /usr/bin/python python /usr/bin/python3 1
#RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.17.5/bin/linux/amd64/kubectl \
#    && chmod a+x kubectl && cp kubectl /usr/local/bin/kubectl

# Some tools like yamllint need this
ENV LANG=C.UTF-8
