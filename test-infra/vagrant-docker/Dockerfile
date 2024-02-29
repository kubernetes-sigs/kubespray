# Docker image published at quay.io/kubespray/vagrant

ARG KUBESPRAY_VERSION
FROM quay.io/kubespray/kubespray:${KUBESPRAY_VERSION}

ENV VAGRANT_VERSION=2.3.7
ENV VAGRANT_DEFAULT_PROVIDER=libvirt
ENV VAGRANT_ANSIBLE_TAGS=facts

RUN apt-get update && apt-get install -y wget libvirt-dev openssh-client rsync git build-essential

# Install Vagrant
RUN wget https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}-1_amd64.deb && \
 dpkg -i vagrant_${VAGRANT_VERSION}-1_amd64.deb && \
 rm vagrant_${VAGRANT_VERSION}-1_amd64.deb && \
 vagrant plugin install vagrant-libvirt
