# Use imutable image tags rather than mutable tags (like ubuntu:20.04)
FROM ubuntu:focal-20220531

ARG ARCH=amd64
ARG TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENV VAGRANT_VERSION=2.2.19
ENV VAGRANT_DEFAULT_PROVIDER=libvirt
ENV VAGRANT_ANSIBLE_TAGS=facts

RUN apt update -y \
    && apt install -y \
    libssl-dev python3-dev sshpass apt-transport-https jq moreutils wget libvirt-dev openssh-client rsync git \
    ca-certificates curl gnupg2 software-properties-common python3-pip unzip \
    && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && add-apt-repository \
    "deb [arch=$ARCH] https://download.docker.com/linux/ubuntu \
    $(lsb_release -cs) \
    stable" \
    && apt update -y && apt-get install --no-install-recommends -y docker-ce \
    && rm -rf /var/lib/apt/lists/*

# Some tools like yamllint need this
# Pip needs this as well at the moment to install ansible
# (and potentially other packages)
# See: https://github.com/pypa/pip/issues/10219
ENV LANG=C.UTF-8

WORKDIR /kubespray
COPY . .
RUN /usr/bin/python3 -m pip install --no-cache-dir pip -U \
    && /usr/bin/python3 -m pip install --no-cache-dir -r tests/requirements.txt \
    && python3 -m pip install --no-cache-dir -r requirements.txt \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 1

RUN KUBE_VERSION=$(sed -n 's/^kube_version: //p' roles/kubespray-defaults/defaults/main.yaml) \
    && curl -LO https://storage.googleapis.com/kubernetes-release/release/$KUBE_VERSION/bin/linux/$ARCH/kubectl \
    && chmod a+x kubectl \
    && mv kubectl /usr/local/bin/kubectl

# Install Vagrant
RUN wget https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}_x86_64.deb && \
 dpkg -i vagrant_${VAGRANT_VERSION}_x86_64.deb && \
 rm vagrant_${VAGRANT_VERSION}_x86_64.deb && \
 vagrant plugin install vagrant-libvirt

# Install Kubernetes collections
RUN pip3 install kubernetes \
    && ansible-galaxy collection install kubernetes.core