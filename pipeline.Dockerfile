# Use imutable image tags rather than mutable tags (like ubuntu:20.04)
FROM ubuntu:focal-20220531

ARG ARCH=amd64

# Some tools like yamllint need this
# Pip needs this as well at the moment to install ansible
# (and potentially other packages)
# See: https://github.com/pypa/pip/issues/10219
ENV VAGRANT_VERSION=2.3.4 \
    VAGRANT_DEFAULT_PROVIDER=libvirt \
    VAGRANT_ANSIBLE_TAGS=facts \ 
    LANG=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive
	
RUN apt update && apt install -y \
    libssl-dev python3-dev python3-pip sshpass apt-transport-https jq moreutils libvirt-dev openssh-client rsync git \
    ca-certificates curl gnupg2 software-properties-common unzip \
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add - \
    && add-apt-repository "deb [arch=$ARCH] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    && apt update && apt install --no-install-recommends -y docker-ce \
    && apt autoremove -yqq --purge && apt clean && rm -rf /var/lib/apt/lists/*

WORKDIR /kubespray

COPY . .

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && pip install --no-cache-dir pip -U \
    && pip install --no-cache-dir -r tests/requirements.txt -r requirements.txt \
    && KUBE_VERSION=$(sed -n 's/^kube_version: //p' roles/kubespray-defaults/defaults/main.yaml) \
    && curl -L https://storage.googleapis.com/kubernetes-release/release/$KUBE_VERSION/bin/linux/$ARCH/kubectl -o /usr/local/bin/kubectl\
    && chmod a+x /usr/local/bin/kubectl \
    # Install Vagrant
    && curl -LO https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}-1_amd64.deb \
    && dpkg -i vagrant_${VAGRANT_VERSION}-1_amd64.deb \
    && rm vagrant_${VAGRANT_VERSION}-1_amd64.deb \
    && vagrant plugin install vagrant-libvirt \
    # Install Kubernetes collections
    && pip install --no-cache-dir kubernetes \
    && ansible-galaxy collection install kubernetes.core \
    # Clean cache python
    && find / -type d -name '*__pycache__' -prune -exec rm -rf {} \;
