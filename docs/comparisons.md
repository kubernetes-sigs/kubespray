Kargo vs [Kops](https://github.com/kubernetes/kops)
---------------

Kargo runs on bare metal and most clouds, using Ansible as its substrate for
provisioning and orchestration. Kops performs the provisioning and orchestration
itself, and as such is less flexible in deployment platforms. For people with
familiarity with Ansible, existing Ansible deployments or the desire to run a
Kubernetes cluster across multiple platforms, Kargo is a good choice. Kops,
however, is more tightly integrated with the unique features of the clouds it
supports so it could be a better choice if you know that you will only be using
one platform for the foreseeable future.

Kargo vs [Kubeadm](https://github.com/kubernetes/kubeadm)
------------------

Kubeadm provides domain Knowledge of Kubernetes clusters' life cycle
management, including self-hosted layouts, dynamic discovery services and so
on. Had it belong to the new [operators world](https://coreos.com/blog/introducing-operators.html),
it would've likely been named a "Kubernetes cluster operator". Kargo however,
does generic configuration management tasks from the "OS operators" ansible
world, plus some initial K8s clustering (with networking plugins included) and
control plane bootstrapping. Kargo [strives](https://github.com/kubernetes-incubator/kargo/issues/553)
to adopt kubeadm as a tool in order to consume life cycle management domain
knowledge from it and offload generic OS configuration things from it, which
hopefully benefits both sides.
