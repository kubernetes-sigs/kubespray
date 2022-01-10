# CI test coverage

To generate this Matrix run `./tests/scripts/md-table/main.py`

## containerd

| OS / CNI | calico | canal | cilium | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
almalinux8 |  :white_check_mark: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: |
amazon |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :white_check_mark: | :x: | :x: | :white_check_mark: | :x: | :white_check_mark: | :x: | :x: |
debian10 |  :white_check_mark: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
debian11 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian9 |  :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: | :x: |
fedora34 |  :white_check_mark: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: |
fedora35 |  :white_check_mark: | :x: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: |
opensuse |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: |
oracle7 |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu16 |  :x: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: | :x: | :x: |
ubuntu18 |  :white_check_mark: | :x: | :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :white_check_mark: |
ubuntu20 |  :white_check_mark: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: |

## crio

| OS / CNI | calico | canal | cilium | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
almalinux8 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian10 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian11 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian9 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora34 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora35 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
oracle7 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu16 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu18 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu20 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |

## docker

| OS / CNI | calico | canal | cilium | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- |
almalinux8 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
debian10 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian11 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian9 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
fedora34 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
fedora35 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
oracle7 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu16 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
ubuntu18 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu20 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
