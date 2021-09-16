import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_service(host):
    svc = host.service("crio")
    assert svc.is_running
    assert svc.is_enabled


def test_run(host):
    crictl = "/usr/local/bin/crictl"
    path = "unix:///var/run/crio/crio.sock"
    with host.sudo():
        cmd = host.command(crictl + " --runtime-endpoint " + path + " version")
    assert cmd.rc == 0
    assert "RuntimeName:  cri-o" in cmd.stdout
