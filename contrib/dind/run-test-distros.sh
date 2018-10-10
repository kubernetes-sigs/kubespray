#!/bin/bash
# Q&D test'em all: creates full DIND kubespray deploys
# for each distro, verifying it via netchecker.

pass_or_fail() {
    local rc="$?"
    local msg="$*"
    local date="$(date -Isec)"
    [ $rc -eq 0 ] && echo "PASS: [$date] $msg" || echo "FAIL: [$date] $msg"
}
test_distro() {
    local distro=${1:?}
    ansible-playbook -i hosts dind-cluster.yaml --extra-vars node_distro=$distro
    pass_or_fail "$distro: dind-nodes"
    (cd ../..
        INVENTORY_DIR=inventory/local-dind
        mkdir -p ${INVENTORY_DIR}
        rm -f ${INVENTORY_DIR}/hosts.ini
        CONFIG_FILE=${INVENTORY_DIR}/hosts.ini /tmp/kubespray.dind.inventory_builder.sh
        ansible-playbook --become -e ansible_ssh_user=$distro -i \
            ${INVENTORY_DIR}/hosts.ini cluster.yml \
            --extra-vars @contrib/dind/kubespray-dind.yaml --extra-vars bootstrap_os=$distro
        pass_or_fail "$distro: kubespray"
    )
    docker exec kube-node1 kubectl get pod --all-namespaces
    pass_or_fail "$distro: kube-api"
    let n=60
    while ((n--)); do
        docker exec kube-node1 curl -s http://localhost:31081/api/v1/connectivity_check | grep successfully && break
        sleep 2
    done
    [ $n -ge 0 ]
    pass_or_fail "$distro: netcheck"
}

# Get all DISTROS from distro.yaml if $* unset (shame no yaml parsing, but nuff anyway)
DISTROS="${*:-$(egrep -o '^  \w+' group_vars/all/distro.yaml|paste -s)}"
NODES="$(egrep ^kube-node hosts|paste -s)"
echo "DISTROS=${DISTROS}"
for distro in ${DISTROS}; do
    docker rm -f ${NODES}
    { time test_distro ${distro} ;} |& tee test-${distro}.out
    # sleeping for the sake of the human to verify if they want
    sleep 2m
done
egrep '^(PASS|FAIL):' test-*.out | sort -k2
