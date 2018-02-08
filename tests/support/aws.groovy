def run(username, credentialsId, ami, network_plugin, aws_access, aws_secret) {
      def inventory_path = pwd() + "/inventory/sample/hosts.ini"
      dir('tests') {
          wrap([$class: 'AnsiColorBuildWrapper', colorMapName: "xterm"]) {
              try {
                  create_vm("${env.JOB_NAME}-${env.BUILD_NUMBER}", inventory_path, ami, username, network_plugin, aws_access, aws_secret)
                  install_cluster(inventory_path, credentialsId, network_plugin)

                  test_apiserver(inventory_path, credentialsId)
                  test_create_pod(inventory_path, credentialsId)
                  test_network(inventory_path, credentialsId)
              } finally {
                  delete_vm(inventory_path, credentialsId, aws_access, aws_secret)
              }
          }
      }
}

def create_vm(run_id, inventory_path, ami, username, network_plugin, aws_access, aws_secret) {
    ansiblePlaybook(
        inventory: 'local_inventory/hosts.cfg',
        playbook: 'cloud_playbooks/create-aws.yml',
        extraVars: [
            test_id: run_id,
            kube_network_plugin: network_plugin,
            aws_access_key: [value: aws_access, hidden: true],
            aws_secret_key: [value: aws_secret, hidden: true],
            aws_ami_id: ami,
            aws_security_group: [value: 'sg-cb0327a2', hidden: true],
            key_name: 'travis-ci',
            inventory_path: inventory_path,
            aws_region: 'eu-central-1',
            ssh_user: username
        ],
        colorized: true
    )
}

def delete_vm(inventory_path, credentialsId, aws_access, aws_secret) {
    ansiblePlaybook(
        inventory: inventory_path,
        playbook: 'cloud_playbooks/delete-aws.yml',
        credentialsId: credentialsId,
        extraVars: [
            aws_access_key: [value: aws_access, hidden: true],
            aws_secret_key: [value: aws_secret, hidden: true]
        ],
        colorized: true
    )
}

def install_cluster(inventory_path, credentialsId, network_plugin) {
    ansiblePlaybook(
        inventory: inventory_path,
        playbook: '../cluster.yml',
        sudo: true,
        credentialsId: credentialsId,
        extraVars: [
            kube_network_plugin: network_plugin
        ],
        extras: "-e cloud_provider=aws",
        colorized: true
    )
}

def test_apiserver(inventory_path, credentialsId) {
    ansiblePlaybook(
        inventory: inventory_path,
        playbook: 'testcases/010_check-apiserver.yml',
        credentialsId: credentialsId,
        colorized: true
    )
}

def test_create_pod(inventory_path, credentialsId) {
    ansiblePlaybook(
        inventory: inventory_path,
        playbook: 'testcases/020_check-create-pod.yml',
        sudo: true,
        credentialsId: credentialsId,
        colorized: true
    )
}

def test_network(inventory_path, credentialsId) {
    ansiblePlaybook(
        inventory: inventory_path,
        playbook: 'testcases/030_check-network.yml',
        sudo: true,
        credentialsId: credentialsId,
        colorized: true
    )
}
return this;
