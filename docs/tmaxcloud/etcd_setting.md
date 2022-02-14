# ETCD command 설정 변경 


- command/--listen-metrics-urls 변경

    etcd 매니페스트 내 .spec.containers[0].command[] 에 `--listen-metrics-urls` 변경 필요시   
    `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`에서 `MAIN_MASTER_IP`에 원하는 IP를 추가한다. 


    ```bash
    # Main master IP that etcd use as command/listen-metrics-urls
    MAIN_MASTER_IP: 127.0.0.1
    ```