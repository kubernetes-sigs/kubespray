## 구성 요소 및 버전

* 모든 node에 필요
  * nss - 3.53.1-17.el8_3
  * conntrack - 1.4.4-10.el8
  * socat - 1.7.3.3-2.el8
  * cri-o-1.19
  * sshpass
  * nfs-utils - 1:2.3.3-41.el8_4.2.x86_64
  * java-1.8.0-openjdk-devel.x86_64

* kubespray install 실행하는 node에만 필요
  * python3-pip-python 3.6
  * python3-cryptography-3.2.1-4.el8 (BaseOS)
  * python3-jinja2- 2.10.1-2.el8_0 (AppStream)
  * python3-netaddr-0.7.19-8.el8 (AppStream)
  * python3-jmespath-0.9.0-11.el8 (AppStream)
  * python3-ruamel-yaml-0.15.41-2.el8 (epel)
  * python3-pbr-5.1.2-3.el8 (epel-release)
  * ansible - 2.9.23-1.el8 (epel)

* private registry node에만 필요
  * podman

## 폐쇄망 구축 가이드
0. 각 호스트에 local-package-repo 구축한다.
  * https://github.com/tmax-cloud/install-pkg-repo/tree/5.0 참고
  * pre-required packages들은 반드시 포함되어있어야 한다.
  
1. 아래 가이드를 참고 하여 image registry를 구축한다.
  * podman을 설치 후 /etc/containers/registries.conf에 insecure registry 등록한다.
    ```bash
    yum install podman
    
    [registires.insecure]
    registries = ['<내부망IP>:<PORT>']
    ex) registries = ['10.0.10.50:5000']
    ```
  * 아래의 ftp에서 supercloud-images.tar와 registry.tar를 다운로드 한다.
    * ftp : 192.168.1.150:/home/ck-ftp/k8s/install/offline/supercloud-images
  * registry.tar를 load 한다.
    ```bash
    $ podman load -i registry.tar
    ```    
  * 다운로드 한 tar 압축을 풀고 해당 host path로 image registry를 띄운다.
    ```bash
    $ tar -xvf supercloud-images.tar
    $ podman run -it -d -p{image registry ip:port}:5000 --privileged -v {image tar 푼 경로}:/var/lib/registry registry
    EX) podman run -it -d -p10.0.10.50:5000:5000 --privileged -v /root/supercloud-registry:/var/lib/registry registry
    ```
* 비고 :
    * 위 내용은 1개의 node에서만 진행한다.

2. 아래 가이드를 참고 하여 file repo를 구축한다.
  * file repo에서 사용할 하위 파일들을 kubespray 실행 노드 특정 디렉토리(ex. /tmp/files-repo)에 배치 준비한다.
    ```bash
    $ mkdir /tmp/files-repo

    https://storage.googleapis.com/kubernetes-release/release/v1.19.4/bin/linux/amd64/kubeadm
    https://storage.googleapis.com/kubernetes-release/release/v1.19.4/bin/linux/amd64/kubectl
    https://storage.googleapis.com/kubernetes-release/release/v1.19.4/bin/linux/amd64/kubelet
    https://github.com/containernetworking/plugins/releases/download/v0.9.1/cni-plugins-linux-amd64-v0.9.1.tgz
    https://github.com/kubernetes-sigs/cri-tools/releases/download/v1.19.0/crictl-v1.19.0-linux-amd64.tar.gz
    https://github.com/projectcalico/calicoctl/releases/download/v3.17.4/calicoctl-linux-amd64
    https://github.com/projectcalico/calico/archive/calico-v3.17.4.tar.gz
    https://github.com/etcd-io/etcd/releases/download/v3.4.13/etcd-v3.4.13-linux-amd64.tar.gz
    https://tmax-cloud.github.io/HyperRegistry-Chart/hyperregistry-v2.2.2.tgz
    https://get.helm.sh/helm-v3.5.4-linux-amd64.tar.gz
    
    ```
   * 아래의 ftp에서 다운로드도 가능하다.
     * ftp : 192.168.1.150:/home/ck-ftp/k8s/install/offline/files-repo
* 비고 :
    * file repo의 디렉토리 변경시에는 kubespray/inventory/tmaxcloud/group_vars/all/offline.yml 의 "files_repo" 부분을 경로에 맞게 수정한다.

3. 아래 가이드를 참고 하여 kubespray 설치를 위한 환경설정을 한다.
  * (kubespray install playbook 실행 하는 노드) sshpass 설치 및 ssh key 배포 한다.
    ```bash
    $ yum -y install sshpass
    $ ssh-keygen -t rsa
    $ ssh-copy-id -i root@<설치할모든노드IP>

    테스트 : ssh 접근이 비밀번호 없이 가능
    ```
  * (모든 노드) resolv.conf 파일 확인 한다.
    * 구축할 모든 노드에 /etc/resolv.conf 파일이 있는지 확인, 없으면 생성  

4. kubespray로 설치할 준비를 한다.
  * (kubespray install playbook 실행 하는 노드) kubespray를 다운로드 한다.
    ```bash
    $ git clone https://github.com/tmax-cloud/kubespray.git
    $ cd kubespray
    $ git checkout tmax-master
    ```
  * (kubespray install playbook 실행 하는 노드) kubespray 의존성 패키지 설치 한다.
    ```bash
    $ yum -y install python3-pip python3-cryptography python3-jinja2 python3-netaddr python3-jmespath python3-ruamel-yaml python3-pbr ansible
    ```

5. kubespray에서 설치할 노드들을 정의한다.
    * kubespray/inventory/tmaxcloud/inventory.ini
      * [all] : all node
        * [hostname] [ansibleip] [backupip]
        ```bash 
          ex) master1 ansible_host=10.0.10.51 ip=10.0.10.51
              master2 ansible_host=10.0.10.52 ip=10.0.10.52
              master3 ansible_host=10.0.10.53 ip=10.0.10.53
              worker1 ansible_host=10.0.10.54 ip=10.0.10.54
              worker2 ansible_host=10.0.10.55 ip=10.0.10.55
              
              bastion ansible_host=192.168.9.1 ip=192.168.9.1
        ```
      * [kube_control_plane] : master node
        ```bash        
         master1
         master2
         master3
        ```        
      * [etcd] : master node (etcd node)
        ```bash        
         master1
         master2
         master3
        ```
      * [kube_node] : worker node
        ```bash        
         node1
         node2
        ```
      * [bastion] : proxy node
        ```bash 
         bastion
        ``` 
    * etcd node를 따로 설정하는 것도 가능하다.
    * [all] 에만 ip를 정의하고, 나머지는 [all]에서 정의한 hostname만 작성한다.
    * LB 없이 master 다중화를 구축하는 경우, 아래 가이드를 통해 모든 master에 keepalived를 추가로 설치한다. 
      * https://github.com/tmax-cloud/install-k8s#step-3-1-kubernetes-cluster-%EB%8B%A4%EC%A4%91%ED%99%94-%EA%B5%AC%EC%84%B1%EC%9D%84-%EC%9C%84%ED%95%9C-keepalived-%EC%84%A4%EC%B9%98-master 
    
6. kubespray에서 사용할 사용자 변수들을 설정한다.
  * https://github.com/tmax-cloud/kubespray/tree/tmax-master/docs/tmaxcloud 에 있는 md를 참고하여 설정한다.
    * 필수 설정 파일
      * all.yml, k8s_cluster.yml, k8s-net-calico.yml, addon.yml, offline.md (offline시에만)

7. kubespray install playbook을 실행한다. (cluster.yml)
  * ex) ansible-playbook -i inventory/tmaxcloud/inventory.ini --become --become-user=root cluster.yml
    * -t 옵션을 주어 cluster.yml에서 tag가 지정된 모듈만 따로 진행 할 수 있다. 
      * ex) ansible-playbook -i inventory/tmaxcloud/inventory.ini --become --become-user=root cluster.yml -t apps
    * worker node 없이 master node만 구성한 경우 -e ignore_assert_errors=yes 옵션을 주어 playbook을 실행한다.
      * ex) ansible-playbook -i inventory/tmaxcloud/inventory.ini --become --become-user=root cluster.yml -e ignore_assert_errors=yes

## 삭제 가이드
0. kubespray uninstall playbook을 실행한다. (reset.yml)
  * ex) ansible-playbook -i inventory/tmaxcloud/inventory.ini --become --become-user=root reset.yml
* 비고 :
  * inventory에 정의된 host에 image registry를 구축했더라면 함께 삭제 되므로 reset 후 클러스터 재설치에는 image registry도 해야 한다.
