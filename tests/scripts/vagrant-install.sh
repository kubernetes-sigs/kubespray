#!/bin/bash

# install_vagrant() {
#  sudo apt install vagrant-libvirt vagrant -y
#  sudo vagrant plugin install vagrant-libvirt
# }

# prep(){
# 	sudo apt-get update -y
# 	sudo apt-get install ca-certificates curl libvirt-daemon-system\
# 		libvirt-clients qemu-utils qemu-kvm htop atop -y

# 	sudo install -m 0755 -d /etc/apt/keyrings
# }
# install_docker() {
# 	VERSION_STRING=5:26.1.0-1~ubuntu.24.04~noble
# 	sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
# 	sudo chmod a+r /etc/apt/keyrings/docker.asc

# 	# Add the repository to Apt sources:
# 	echo \
# 		"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
# 		$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
# 			sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
# 	sudo apt-get update -y

# 	sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
# }
# install_docker_auto () {
# 	 curl -fsSL https://get.docker.com -o get-docker.sh
# 	 sudo sh ./get-docker.sh --dry-run
# }



VAGRANT_VERSION=2.4.1
VAGRANT_DEFAULT_PROVIDER=libvirt
VAGRANT_ANSIBLE_TAGS=facts
LANG=C.UTF-8
DEBIAN_FRONTEND=noninteractive
PYTHONDONTWRITEBYTECODE=1
KUBE_VERSION=1.29.5
pipeline_install() {
    cp /etc/apt/sources.list /etc/apt/sources.list."$(date +"%F")"
    sed -i -e '/^# deb-src.*universe$/s/# //g' /etc/apt/sources.list
    sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources

    apt update
    # libssl-dev \
        # python3-dev \
        #         # jq \
        # moreutils \
        # libvirt-dev \
        #         # rsync \
        # git \
        #                 # htop \
        # gpg \
        # atop

        # gnupg2 \
# software-properties-common
#
    apt install --no-install-recommends -y \
        git \
        make \
        python3-pip \
        sshpass \
        apt-transport-https \
        openssh-client \
        ca-certificates \
        curl \
        libfuse2 \
        unzip \
        qemu-utils \
        libvirt-daemon-system \
        libvirt-clients \
        qemu-kvm \
        ebtables libguestfs-tools \
        ruby-fog-libvirt \
        libvirt-dev \
        gcc \
        build-essential \
        ruby-libvirt \
        libxslt-dev libxml2-dev zlib1g-dev \
        python3-venv python3-full \
        dnsmasq

    apt-get build-dep -y ruby-libvirt ruby-dev
    ### VAGRANT ###
    # apt-get install -y unzip
    curl -LO https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}_linux_amd64.zip
    unzip vagrant_${VAGRANT_VERSION}_linux_amd64.zip
    mv vagrant /usr/local/bin/vagrant
    chmod a+x /usr/local/bin/vagrant
    # ls -la /usr/local/bin/vagrant
    /usr/local/bin/vagrant plugin install vagrant-libvirt
    usermod -aG kvm kubespray
    usermod -aG libvirt kubespray

    ### DOCKER ###
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository -y "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
    apt update
    apt install --no-install-recommends -y docker-ce
    apt autoremove -y --purge && apt clean && rm -rf /var/lib/apt/lists/* /var/log/*

    ### KUBECTL ###
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    mv kubectl /usr/local/bin/kubectl
    chmod a+x /usr/local/bin/kubectl
    systemctl restart libvirtd
    # Install Vagrant
     # apt update -y
    # echo apt-get install -y unzip libfuse2 vagrant vagrant-libvirt
    # apt --fix-broken install -y
    # dpkg --configure -a -y


}
# wrapped up in a function so that we have some protection against only getting
# half the file during "curl | sh"
pipeline_install
