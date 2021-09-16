#!/bin/bash
# Q&D test'em all: creates full DIND kubespray deploys
# for each distro, verifying it via netchecker.

info() {
    local msg="$*"
    local date="$(date -Isec)"
    echo "INFO: [$date] $msg"
}
pass_or_fail() {
    local rc="$?"
    local msg="$*"
    local date="$(date -Isec)"
    [ $rc -eq 0 ] && echo "PASS: [$date] $msg" || echo "FAIL: [$date] $msg"
    return $rc
}
test_distro() {
    local distro=${1:?};shift
    local extra="${*:-}"
    local prefix="$distro[${extra}]}"
    ansible-playbook -i hosts dind-cluster.yaml -e node_distro=$distro
    pass_or_fail "$prefix: dind-nodes" || return 1
    (cd ../..
        INVENTORY_DIR=inventory/local-dind
        mkdir -p ${INVENTORY_DIR}
        rm -f ${INVENTORY_DIR}/hosts.ini
        CONFIG_FILE=${INVENTORY_DIR}/hosts.ini /tmp/kubespray.dind.inventory_builder.sh
        # expand $extra with -e in front of each word
        extra_args=""; for extra_arg in $extra; do extra_args="$extra_args -e $extra_arg"; done
        ansible-playbook --become -e ansible_ssh_user=$distro -i \
            ${INVENTORY_DIR}/hosts.ini cluster.yml \
            -e @contrib/dind/kubespray-dind.yaml -e bootstrap_os=$distro ${extra_args}
        pass_or_fail "$prefix: kubespray"
    ) || return 1
    local node0=${NODES[0]}
    docker exec ${node0} kubectl get pod --all-namespaces
    pass_or_fail "$prefix: kube-api" || return 1
    let retries=60
    while ((retries--)); do
        # Some CNI may set NodePort on "main" node interface address (thus no localhost NodePort)
        # e.g. kube-router: https://github.com/cloudnativelabs/kube-router/pull/217
        docker exec ${node0} curl -m2 -s http://${NETCHECKER_HOST:?}:31081/api/v1/connectivity_check | grep successfully && break
        sleep 2
    done
    [ $retries -ge 0 ]
    pass_or_fail "$prefix: netcheck" || return 1
}

NODES=($(egrep ^kube_node hosts))
NETCHECKER_HOST=localhost

: ${OUTPUT_DIR:=./out}
mkdir -p ${OUTPUT_DIR}

# The SPEC file(s) must have two arrays as e.g.
# DISTROS=(debian centos)
# EXTRAS=(
#     'kube_network_plugin=calico'
#     'kube_network_plugin=flannel'
#     'kube_network_plugin=weave'
# )
# that will be tested in a "combinatory" way (e.g. from above there'll be
# be 6 test runs), creating a sequenced <spec_filename>-nn.out with each output.
#
# Each $EXTRAS element will be whitespace split, and passed as --extra-vars
# to main kubespray ansible-playbook run.

SPECS=${*:?Missing SPEC files, e.g. test-most_distros-some_CNIs.env}
for spec in ${SPECS}; do
    unset DISTROS EXTRAS
    echo "Loading file=${spec} ..."
    . ${spec} || continue
    : ${DISTROS:?} || continue
    echo "DISTROS=${DISTROS[@]}"
    echo "EXTRAS->"
    printf "  %s\n" "${EXTRAS[@]}"
    let n=1
    for distro in ${DISTROS[@]}; do
        for extra in "${EXTRAS[@]:-NULL}"; do
            # Magic value to let this for run once:
            [[ ${extra} == NULL ]] && unset extra
            docker rm -f ${NODES[@]}
            printf -v file_out "%s/%s-%02d.out" ${OUTPUT_DIR} ${spec} $((n++))
            {
                info "${distro}[${extra}] START: file_out=${file_out}"
                time test_distro ${distro} ${extra}
            } |& tee ${file_out}
            # sleeping for the sake of the human to verify if they want
            sleep 2m
        done
    done
done
egrep -H '^(....:|real)' $(ls -tr ${OUTPUT_DIR}/*.out)
