# CI test coverage

To generate this Matrix run `./tests/scripts/md-table/main.py`

## containerd

| OS / CNI | calico | cilium | custom_cni | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
almalinux8 |  :white_check_mark: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: |
amazon |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :white_check_mark: | :x: | :x: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: |
debian10 |  :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :x: | :white_check_mark: | :x: |
debian11 |  :white_check_mark: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
debian12 |  :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora37 |  :white_check_mark: | :x: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: |
fedora38 |  :x: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux8 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux9 |  :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu20 |  :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: |
ubuntu22 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |

## crio

| OS / CNI | calico | cilium | custom_cni | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
almalinux8 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian10 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian11 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian12 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora37 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora38 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux8 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux9 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu20 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu22 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |

## docker

| OS / CNI | calico | cilium | custom_cni | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
almalinux8 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian10 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian11 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian12 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora37 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora38 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
opensuse |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux8 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux9 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu20 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
ubuntu22 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
