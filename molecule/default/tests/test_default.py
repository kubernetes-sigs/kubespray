import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_docker_service(host):
    docker = host.service("docker")
    assert docker.is_running
    assert docker.is_enabled


def test_docker_run(host):
    with host.sudo():
        cmd = host.command("docker run hello-world")
    assert cmd.rc == 0
    assert "Hello from Docker!" in cmd.stdout

def test_etcd_service(host):
    docker = host.service("etcd")
    assert docker.is_running
    assert docker.is_enabled


def test_etcdctl(host):
    cmd = host.command("etcdctl --version")
    assert cmd.rc == 0
    assert "etcdctl version: 3." in cmd.stdout

def test_kubectl(host):
    cmd = host.command("sudo -H kubectl version")
    assert cmd.rc == 0
    assert "Client Version:" in cmd.stdout
    assert "Server Version:" in cmd.stdout

def test_run_pod(host):
    cmd = host.command("sudo -H kubectl run --image=nginx:alpine --wait nginx")
    assert cmd.rc == 0
    assert "pod/nginx created" in cmd.stdout