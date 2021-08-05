# Metallb 설정
kubespray로 metallb 설치를 위해 설정해줘야 할 변수 값을 몇개 있습니다.

- Enable ARP 모드:  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`
  ```yaml
  kube_proxy_strict_arp: true
  ```

- Enable Metallb addon:  
  파일: `inventory/tmaxcloud/group_vars/k8s_cluster/addons.yml`
  ```yaml
  metallb_enabled: true
  metallb_ip_range:
    - "172.22.8.160-172.22.8.180"
    - "172.22.8.184-172.22.8.190"
  metallb_version: v0.8.2
  metallb_protocol: "layer2"
  ```
  **metallb_ip_range** 변수 값은 metallb에서 사용할 대역 설정하면 됩니다. (호스트와 동일한 대역 사용)
