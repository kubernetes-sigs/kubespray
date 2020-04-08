# Comparison

## Kubespray vs [Kops](https://github.com/kubernetes/kops)

Kubespray runs on bare metal and most clouds, using Ansible as its substrate for
provisioning and orchestration. Kops performs the provisioning and orchestration
itself, and as such is less flexible in deployment platforms. For people with
familiarity with Ansible, existing Ansible deployments or the desire to run a
Kubernetes cluster across multiple platforms, Kubespray is a good choice. Kops,
however, is more tightly integrated with the unique features of the clouds it
supports so it could be a better choice if you know that you will only be using
one platform for the foreseeable future.

## Kubespray vs [Kubeadm](https://github.com/kubernetes/kubeadm)

Kubeadm provides domain Knowledge of Kubernetes clusters' life cycle
management, including self-hosted layouts, dynamic discovery services and so
on. Had it belonged to the new [operators world](https://coreos.com/blog/introducing-operators.html),
it may have been named a "Kubernetes cluster operator". Kubespray however,
does generic configuration management tasks from the "OS operators" ansible
world, plus some initial K8s clustering (with networking plugins included) and
control plane bootstrapping.

Kubespray supports `kubeadm` for cluster creation since v2.3
(and deprecated non-kubeadm deployment starting from v2.8)
in order to consume life cycle management domain knowledge from it
and offload generic OS configuration things from it, which hopefully benefits both sides.
