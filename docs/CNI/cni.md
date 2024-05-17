CNI
==============

This network plugin only unpacks CNI plugins version `cni_version` into `/opt/cni/bin` and instructs implementation of container runtime cri to use cni.

It's intended usage is for custom CNI configuration, e.g. manual routing tables + bridge + loopback CNI plugin outside kubespray scope. Furthermore, it's used for non-kubespray supported CNI plugins which you can install afterward.

You are required to fill `/etc/cni/net.d` with valid CNI configuration after using kubespray.
