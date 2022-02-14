# Kube-scheduler 설정 변경

- command/--port=0 삭제 

    kube-scheduler .spec.containers[0].command[]에 `--port=0` 삭제 필요시 
    `inventory/tmaxcloud/group_vars/k8s_cluster/k8s-cluster.yml`에서 `scheduler_port_0`을 false로 변경한다. 

    ```bash
    # check if kube-scheduler's command/port=0 exists
    scheduler_port_0: false
    ```