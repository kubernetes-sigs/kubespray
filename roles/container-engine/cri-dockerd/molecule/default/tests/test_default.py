import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_run_pod(host):
    run_command = "/usr/local/bin/crictl run --with-pull /tmp/container.json /tmp/sandbox.json"
    with host.sudo():
        cmd = host.command(run_command)
    assert cmd.rc == 0

    with host.sudo():
      log_f = host.file("/tmp/cri-dockerd1.0.log")

      assert log_f.exists
      assert b"Hello from Docker" in log_f.content
