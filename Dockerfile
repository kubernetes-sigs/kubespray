# Use imutable image tags rather than mutable tags (like ubuntu:22.04)
FROM ubuntu:jammy-20230308
# Some tools like yamllint need this
# Pip needs this as well at the moment to install ansible
# (and potentially other packages)
# See: https://github.com/pypa/pip/issues/10219
ENV LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /kubespray
COPY *.yml ./
COPY *.cfg ./
COPY roles ./roles
COPY contrib ./contrib
COPY inventory ./inventory
COPY library ./library
COPY extra_playbooks ./extra_playbooks
COPY playbooks ./playbooks
COPY plugins ./plugins

RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
   apt update -q \
   && apt install -yq --no-install-recommends \
       curl \
       python3 \
       python3-pip \
       sshpass \
       vim \
       rsync \
       openssh-client \
    && pip install --no-compile --no-cache-dir -r requirements.txt \
    && KUBE_VERSION=$(sed -n 's/^kube_version: //p' roles/kubespray-defaults/defaults/main/main.yml) \
    && curl -L https://dl.k8s.io/release/$KUBE_VERSION/bin/linux/$(dpkg --print-architecture)/kubectl -o /usr/local/bin/kubectl \
    && echo $(curl -L https://dl.k8s.io/release/$KUBE_VERSION/bin/linux/$(dpkg --print-architecture)/kubectl.sha256) /usr/local/bin/kubectl | sha256sum --check \
    && chmod a+x /usr/local/bin/kubectl \
    && rm -rf /var/lib/apt/lists/* /var/log/* \
    && find /usr -type d -name '*__pycache__' -prune -exec rm -rf {} \;
