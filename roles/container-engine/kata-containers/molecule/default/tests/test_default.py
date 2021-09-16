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


def test_run_pod(host):
    image = "docker.io/library/hello-world:latest"
    runtime = "io.containerd.kata-qemu.v2"

    pull_command = "ctr image pull {}".format(image)
    with host.sudo():
        cmd = host.command(pull_command)
    assert cmd.rc == 0

    run_command = "ctr run --runtime {} {} kata1".format(runtime, image)
    with host.sudo():
        cmd = host.command(run_command)
    assert cmd.rc == 0
    assert "Hello from Docker!" in cmd.stdout
