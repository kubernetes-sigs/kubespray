# CI test coverage

To generate this Matrix run `./tests/scripts/md-table/main.py`

## docker

| OS / CNI | calico | canal | cilium | contiv | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- | --- |
amazon |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
centos7 |  :white_check_mark: | :x: | :x: | :x: | :x: | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: |
coreos |  :white_check_mark: | :white_check_mark: | :white_check_mark: | :x: | :x: | :x: | :white_check_mark: | :x: | :white_check_mark: |
debian10 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian9 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: | :x: |
opensuse |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
oracle |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
oracle7 |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rhel7 |  :x: | :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :white_check_mark: |
ubuntu |  :x: | :white_check_mark: | :x: | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: |
ubuntu16 |  :x: | :white_check_mark: | :x: | :white_check_mark: | :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: |
ubuntu18 |  :white_check_mark: | :x: | :white_check_mark: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: |

## containerd

| OS / CNI | calico | canal | cilium | contiv | flannel | kube-ovn | kube-router | macvlan | weave |
|---| --- | --- | --- | --- | --- | --- | --- | --- | --- |
amazon |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
centos7 |  :x: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: |
coreos |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian10 |  :white_check_mark: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
debian9 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
opensuse |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
oracle |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
oracle7 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
rhel7 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu16 |  :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: | :x: |
ubuntu18 |  :x: | :x: | :x: | :x: | :white_check_mark: | :x: | :x: | :x: | :x: |
