#!/bin/bash

echo -e "Kubernetes version: `curl -L -s https://dl.k8s.io/release/stable.txt`\n"
curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm/kubelet.sha256"|echo -e "kubelet_checksum arm\n `cat kubelet.sha256 && rm -f kubelet.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubelet.sha256"|echo -e "kubelet_checksum arm64\n `cat kubelet.sha256 && rm -f kubelet.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubelet.sha256"|echo -e "kubelet_checksum amd64\n `cat kubelet.sha256 && rm -f kubelet.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/ppc64le/kubelet.sha256"|echo -e "kubelet_checksum ppc64le\n `cat kubelet.sha256 && rm -f kubelet.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm/kubectl.sha256"|echo -e "kubectl_checksum arm\n `cat kubectl.sha256 && rm -f kubectl.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubectl.sha256"|echo -e "kubectl_checksum arm64\n `cat kubectl.sha256 && rm -f kubectl.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"|echo -e "kubectl_checksum amd64\n `cat kubectl.sha256 && rm -f kubectl.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/ppc64le/kubectl.sha256"|echo -e "kubectl_checksum ppc64le\n `cat kubectl.sha256 && rm -f kubectl.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm/kubeadm.sha256"|echo -e "kubeadm_checksum arm\n `cat kubeadm.sha256 && rm -f kubeadm.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/arm64/kubeadm.sha256"|echo -e "kubeadm_checksum arm64\n `cat kubeadm.sha256 && rm -f kubeadm.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubeadm.sha256"|echo -e "kubeadm_checksum amd64\n `cat kubeadm.sha256 && rm -f kubeadm.sha256`\n"

curl -sLO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/ppc64le/kubeadm.sha256"|echo -e "kubeadm_checksum ppc64le\n `cat kubeadm.sha256 && rm -f kubeadm.sha256`\n"
