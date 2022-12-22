# Use imutable image tags rather than mutable tags (like ubuntu:20.04)
FROM ubuntu:focal-20220531

ARG ARCH=amd64
ARG TZ=Etc/UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update -y \
    && apt install -y \
    curl python3 python3-pip sshpass \
    && rm -rf /var/lib/apt/lists/*

# Some tools like yamllint need this
# Pip needs this as well at the moment to install ansible
# (and potentially other packages)
# See: https://github.com/pypa/pip/issues/10219
ENV LANG=C.UTF-8

WORKDIR /kubespray
COPY *yml /kubespray/
COPY roles /kubespray/roles
COPY inventory /kubespray/inventory
COPY library /kubespray/library
COPY extra_playbooks /kubespray/extra_playbooks

RUN python3 -m pip install --no-cache-dir \
    ansible==5.7.1 \
    ansible-core==2.12.5 \
    cryptography==3.4.8 \
    jinja2==2.11.3 \
    netaddr==0.7.19 \
    MarkupSafe==1.1.1 \
    && KUBE_VERSION=$(sed -n 's/^kube_version: //p' roles/kubespray-defaults/defaults/main.yaml) \
    && curl -LO https://storage.googleapis.com/kubernetes-release/release/$KUBE_VERSION/bin/linux/$ARCH/kubectl \
    && chmod a+x kubectl \
    && mv kubectl /usr/local/bin/kubectl
