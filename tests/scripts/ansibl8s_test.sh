#! /bin/bash

global_setup() {
  git clone https://github.com/ansibl8s/setup-kubernetes.git setup-kubernetes
  private_key=""
  if [ ! -z ${PRIVATE_KEY_FILE} ]
  then
    private_key="--private-key=${PRIVATE_KEY_FILE}"
  fi
  ansible-playbook create.yml -i hosts -u admin -s \
      -e test_id=${TEST_ID} \
      -e kube_network_plugin=${KUBE_NETWORK_PLUGIN} \
      -e aws_access_key=${AWS_ACCESS_KEY} \
      -e aws_secret_key=${AWS_SECRET_KEY} \
      -e aws_ami_id=${AWS_AMI_ID} \
      -e aws_security_group=${AWS_SECURITY_GROUP} \
      -e key_name=${AWS_KEY_PAIR_NAME} \
      -e inventory_path=${PWD}/inventory.ini \
      -e aws_region=${AWS_REGION}
}

global_teardown() {
  if [ -f inventory.ini ];
  then
    ansible-playbook -i inventory.ini -u admin delete.yml
  fi
  rm -rf ${PWD}/setup-kubernetes
}

should_deploy_cluster() {
  ansible-playbook -i inventory.ini -s ${private_key} -e kube_network_plugin=${KUBE_NETWORK_PLUGIN} setup-kubernetes/cluster.yml

  assertion__status_code_is_success $?
}

should_api_server_respond() {
  ansible-playbook -i inventory.ini ${private_key} testcases/010_check-apiserver.yml

  assertion__status_code_is_success $?
}

should_pod_be_in_expected_subnet() {
  ansible-playbook -i inventory.ini -s ${private_key} testcases/030_check-network.yml -vv

  assertion__status_code_is_success $?
}

should_resolve_cluster_dns() {
  ansible-playbook -i inventory.ini -s ${private_key} testcases/040_check-network-adv.yml -vv

  assertion__status_code_is_success $?
}
