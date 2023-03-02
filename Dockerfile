# Use imutable image tags rather than mutable tags (like ubuntu:20.04)
FROM ubuntu:focal-20220531
# Some tools like yamllint need this
# Pip needs this as well at the moment to install ansible
# (and potentially other packages)
# See: https://github.com/pypa/pip/issues/10219
ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive
ARG ARCH=amd64

WORKDIR /kubespray
COPY *yml .
COPY roles ./roles
COPY contrib ./contrib
COPY inventory ./inventory
COPY library ./library
COPY extra_playbooks ./extra_playbooks

RUN apt update && apt install -y --no-install-recommends \
    curl python3 python3-pip sshpass vim rsync openssh-client \
    && rm -rf /var/lib/apt/lists/* /var/log/* \
    && pip install --no-cache-dir \
    ansible==5.7.1 \
    ansible-core==2.12.5 \
    cryptography==3.4.8 \
    jinja2==2.11.3 \
    netaddr==0.7.19 \
    jmespath==1.0.1 \
    MarkupSafe==1.1.1 \
    ruamel.yaml==0.17.21 \
    && find / -type d -name '*__pycache__' -prune -exec rm -rf {} \; \
    && KUBE_VERSION=$(sed -n 's/^kube_version: //p' roles/kubespray-defaults/defaults/main.yaml) \
    && curl -L https://storage.googleapis.com/kubernetes-release/release/$KUBE_VERSION/bin/linux/$ARCH/kubectl -o /usr/local/bin/kubectl \
    && chmod a+x /usr/local/bin/kubectl
