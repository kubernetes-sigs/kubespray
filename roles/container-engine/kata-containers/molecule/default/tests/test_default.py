import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_run(host):
    kataruntime = "/opt/kata/bin/kata-runtime"
    with host.sudo():
        cmd = host.command(kataruntime + " version")
    assert cmd.rc == 0
    assert "kata-runtime" in cmd.stdout


def test_run_check(host):
    kataruntime = "/opt/kata/bin/kata-runtime"
    with host.sudo():
        cmd = host.command(kataruntime + " check")
    assert cmd.rc == 0
    assert "System is capable of running" in cmd.stdout


def test_run_pod(host):
    runtime = "kata-qemu"

    run_command = "/usr/local/bin/crictl run --with-pull --runtime {} /tmp/container.json /tmp/sandbox.json".format(runtime)
    with host.sudo():
        cmd = host.command(run_command)
    assert cmd.rc == 0

    with host.sudo():
      log_f = host.file("/tmp/kata1.0.log")

      assert log_f.exists
      assert b"Hello from Docker" in log_f.content
