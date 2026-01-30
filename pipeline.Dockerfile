# Use immutable image tags rather than mutable tags (like ubuntu:24.04)
FROM ubuntu:noble-20260113@sha256:cd1dba651b3080c3686ecf4e3c4220f026b521fb76978881737d24f200828b2b
# Some tools like yamllint need this
# Pip needs this as well at the moment to install ansible
# (and potentially other packages)
# See: https://github.com/pypa/pip/issues/10219
ENV VAGRANT_VERSION=2.4.1 \
    VAGRANT_DEFAULT_PROVIDER=libvirt \
    VAGRANT_ANSIBLE_TAGS=facts \
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1

RUN apt update -q \
    && apt install -yq \
         libssl-dev \
         python3-dev \
         python3-pip \
         sshpass \
         apt-transport-https \
         jq \
         moreutils \
         libvirt-dev \
         openssh-client \
         rsync \
         git \
         ca-certificates \
         curl \
         gnupg2 \
         software-properties-common \
         unzip \
         libvirt-clients \
         qemu-utils \
         qemu-kvm \
         dnsmasq \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && add-apt-repository "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    && apt update -q \
    && apt install --no-install-recommends -yq docker-ce \
    && apt autoremove -yqq --purge && apt clean && rm -rf /var/lib/apt/lists/* /var/log/*

WORKDIR /kubespray
ADD ./requirements.txt  /kubespray/requirements.txt
ADD ./tests/requirements.txt /kubespray/tests/requirements.txt

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && pip install --break-system-packages --ignore-installed --no-compile --no-cache-dir pip -U \
    && pip install --break-system-packages --no-compile --no-cache-dir -r tests/requirements.txt \
    && curl -L https://dl.k8s.io/release/v1.34.3/bin/linux/$(dpkg --print-architecture)/kubectl -o /usr/local/bin/kubectl \
    && echo $(curl -L https://dl.k8s.io/release/v1.34.3/bin/linux/$(dpkg --print-architecture)/kubectl.sha256) /usr/local/bin/kubectl | sha256sum --check \
    && chmod a+x /usr/local/bin/kubectl \
    # Install Vagrant
    && curl -LO https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}-1_$(dpkg --print-architecture).deb \
    && dpkg -i vagrant_${VAGRANT_VERSION}-1_$(dpkg --print-architecture).deb \
    && rm vagrant_${VAGRANT_VERSION}-1_$(dpkg --print-architecture).deb \
    && vagrant plugin install vagrant-libvirt \
    # Install Kubernetes collections
    && pip install --break-system-packages --no-compile --no-cache-dir kubernetes \
    && ansible-galaxy collection install kubernetes.core
