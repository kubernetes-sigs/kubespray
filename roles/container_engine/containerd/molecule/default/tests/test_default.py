import os
import pytest

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_service(host):
    svc = host.service("containerd")
    assert svc.is_running
    assert svc.is_enabled


def test_version(host):
    crictl = "/usr/local/bin/crictl"
    path = "unix:///var/run/containerd/containerd.sock"
    with host.sudo():
        cmd = host.command(crictl + " --runtime-endpoint " + path + " version")
    assert cmd.rc == 0
    assert "RuntimeName:  containerd" in cmd.stdout


@pytest.mark.parametrize('image, dest', [
    ('quay.io/kubespray/hello-world:latest', '/tmp/hello-world.tar')
])
def test_image_pull_save_load(host, image, dest):
    nerdctl = "/usr/local/bin/nerdctl"
    dest_file = host.file(dest)

    with host.sudo():
        pull_cmd = host.command(nerdctl + " pull " + image)
    assert pull_cmd.rc ==0

    with host.sudo():
        save_cmd = host.command(nerdctl + " save -o " + dest + " " + image)
    assert save_cmd.rc == 0
    assert dest_file.exists

    with host.sudo():
        load_cmd = host.command(nerdctl + " load < " + dest)
    assert load_cmd.rc == 0


@pytest.mark.parametrize('image', [
    ('quay.io/kubespray/hello-world:latest')
])
def test_run(host, image):
    nerdctl = "/usr/local/bin/nerdctl"

    with host.sudo():
        cmd = host.command(nerdctl + " -n k8s.io run " + image)
    assert cmd.rc == 0
    assert "Hello from Docker" in cmd.stdout
