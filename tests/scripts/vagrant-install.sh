#!/bin/sh

install_vagrant() {
 sudo apt install vagrant-libvirt vagrant -y
 sudo vagrant plugin install vagrant-libvirt
}

prep(){
	sudo apt-get update -y
	sudo apt-get install ca-certificates curl libvirt-daemon-system\
		libvirt-clients qemu-utils qemu-kvm htop atop -y

	sudo install -m 0755 -d /etc/apt/keyrings
}
install_docker() {
	VERSION_STRING=5:26.1.0-1~ubuntu.24.04~noble
	sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
	sudo chmod a+r /etc/apt/keyrings/docker.asc

	# Add the repository to Apt sources:
	echo \
		"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
		$(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
			sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
	sudo apt-get update -y

	sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
}
install_docker_auto () {
	 curl -fsSL https://get.docker.com -o get-docker.sh
	 sudo sh ./get-docker.sh --dry-run
}
do_install() {
	install_vagrant
	install_docker

}



VAGRANT_VERSION=2.3.7
VAGRANT_DEFAULT_PROVIDER=libvirt
VAGRANT_ANSIBLE_TAGS=facts
LANG=C.UTF-8
DEBIAN_FRONTEND=noninteractive
PYTHONDONTWRITEBYTECODE=1
KUBE_VERSION=1.29.5
pipeline_install() {
apt update -q \
apt install -yq \
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
         qemu-utils
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
apt update -q
apt install --no-install-recommends -yq docker-ce
apt autoremove -yqq --purge && apt clean && rm -rf /var/lib/apt/lists/* /var/log/*

curl -L https://dl.k8s.io/release/$KUBE_VERSION/bin/linux/$(dpkg --print-architecture)/kubectl -o /usr/local/bin/kubectl \
echo $(curl -L https://dl.k8s.io/release/$KUBE_VERSION/bin/linux/$(dpkg --print-architecture)/kubectl.sha256) /usr/local/bin/kubectl | sha256sum --check \
chmod a+x /usr/local/bin/kubectl
    # Install Vagrant
curl -LO https://releases.hashicorp.com/vagrant/${VAGRANT_VERSION}/vagrant_${VAGRANT_VERSION}-1_$(dpkg --print-architecture).deb
dpkg -i vagrant_${VAGRANT_VERSION}-1_$(dpkg --print-architecture).deb
rm vagrant_${VAGRANT_VERSION}-1_$(dpkg --print-architecture).deb
vagrant plugin install vagrant-libvirt
}
# wrapped up in a function so that we have some protection against only getting
# half the file during "curl | sh"
pipeline_install
