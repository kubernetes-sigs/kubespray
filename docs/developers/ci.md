# CI test coverage

To generate this Matrix run `./tests/scripts/md-table/main.py`

## containerd

| OS / CNI | calico | cilium | custom_cni | flannel | kube-ovn | kube-router |
|---| --- | --- | --- | --- | --- | --- |
almalinux9 |  :white_check_mark: | :x: | :x: | :x: | :white_check_mark: | :x: |
amazon |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
debian12 |  :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: | :x: | :x: |
debian13 |  :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: | :x: | :x: |
fedora42 |  :white_check_mark: | :x: | :x: | :x: | :x: | :white_check_mark: |
fedora43 |  :white_check_mark: | :x: | :x: | :x: | :x: | :white_check_mark: |
flatcar4081 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
openeuler24 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
rockylinux10 |  :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :x: |
rockylinux9 |  :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :x: |
ubuntu22 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
ubuntu24 |  :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: |

## crio

| OS / CNI | calico | cilium | custom_cni | flannel | kube-ovn | kube-router |
|---| --- | --- | --- | --- | --- | --- |
almalinux9 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: |
debian12 |  :x: | :x: | :x: | :x: | :x: | :x: |
debian13 |  :x: | :x: | :x: | :x: | :x: | :x: |
fedora42 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
fedora43 |  :white_check_mark: | :x: | :x: | :white_check_mark: | :x: | :x: |
flatcar4081 |  :x: | :x: | :x: | :x: | :x: | :x: |
openeuler24 |  :x: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux10 |  :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux9 |  :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu22 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
ubuntu24 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |

## docker

| OS / CNI | calico | cilium | custom_cni | flannel | kube-ovn | kube-router |
|---| --- | --- | --- | --- | --- | --- |
almalinux9 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: |
debian12 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
debian13 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
fedora42 |  :x: | :x: | :x: | :x: | :x: | :x: |
fedora43 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
flatcar4081 |  :x: | :x: | :x: | :x: | :x: | :x: |
openeuler24 |  :x: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux10 |  :x: | :x: | :x: | :x: | :x: | :x: |
rockylinux9 |  :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu22 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
ubuntu24 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: |
