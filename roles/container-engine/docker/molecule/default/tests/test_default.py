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
