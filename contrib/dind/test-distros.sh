#!/bin/bash
# Q&D test'em all: creates full DIND kubespray deploys
# for each distro, verifying it via netchecker.

DISTROS="${*:-debian ubuntu centos fedora}"

test_distro() {
    local distro=${1:?}
    ansible-playbook -i hosts dind-cluster.yaml --extra-vars node_distro=$distro
    (cd ../..
        INVENTORY_DIR=inventory/local-dind
        mkdir -p ${INVENTORY_DIR}
        rm -f ${INVENTORY_DIR}/hosts.ini
        CONFIG_FILE=${INVENTORY_DIR}/hosts.ini /tmp/kubespray.dind.inventory_builder.sh
        ansible-playbook --become -e ansible_ssh_user=$distro -i \
            ${INVENTORY_DIR}/hosts.ini cluster.yml \
            --extra-vars @contrib/dind/kubespray-dind.yaml --extra-vars bootstrap_os=$distro
        [ $? -eq 0 ] && echo PASS: kubespray: $distro || echo FAIL: kubespray: $distro
    )
    docker exec kube-node1 kubectl get pod --all-namespaces
    [ $? -eq 0 ] && echo PASS: kube-api: $distro || echo FAIL: kube-api: $distro
    let n=60
    while ((n--)); do
        docker exec kube-node1 curl -s http://localhost:31081/api/v1/connectivity_check | grep successfully && break
        sleep 2
    done
    [ $n -ge 0 ] && echo PASS: netcheck: $distro || echo FAIL: netcheck: $distro
}

for distro in ${DISTROS}; do
    docker rm -f kube-node{1..5}
    time test_distro ${distro} |& tee test-${distro}.out
    # sleeping for the sake of the human to verify if they want
    sleep 2m
done
egrep '^(PASS|FAIL):' test-*.out
