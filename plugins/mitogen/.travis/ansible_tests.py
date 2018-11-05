#!/usr/bin/env python
# Run tests/ansible/all.yml under Ansible and Ansible-Mitogen

import os
import sys

import ci_lib
from ci_lib import run


BASE_PORT = 2201
TESTS_DIR = os.path.join(ci_lib.GIT_ROOT, 'tests/ansible')
HOSTS_DIR = os.path.join(ci_lib.TMP, 'hosts')


with ci_lib.Fold('docker_setup'):
    for i, distro in enumerate(ci_lib.DISTROS):
        try:
            run("docker rm -f target-%s", distro)
        except: pass

        run("""
            docker run
            --rm
            --detach
            --publish 0.0.0.0:%s:22/tcp
            --hostname=target-%s
            --name=target-%s
            mitogen/%s-test
        """, BASE_PORT + i, distro, distro, distro)


with ci_lib.Fold('job_setup'):
    os.chdir(TESTS_DIR)
    os.chmod('../data/docker/mitogen__has_sudo_pubkey.key', int('0600', 7))

    run("pip install -qr requirements.txt")  # tests/ansible/requirements
    # Don't set -U as that will upgrade Paramiko to a non-2.6 compatible version.
    run("pip install -q ansible==%s", ci_lib.ANSIBLE_VERSION)

    run("mkdir %s", HOSTS_DIR)
    run("ln -s %s/hosts/common-hosts %s", TESTS_DIR, HOSTS_DIR)

    with open(os.path.join(HOSTS_DIR, 'target'), 'w') as fp:
        fp.write('[test-targets]\n')
        for i, distro in enumerate(ci_lib.DISTROS):
            fp.write("target-%s "
                     "ansible_host=%s "
                     "ansible_port=%s "
                     "ansible_user=mitogen__has_sudo_nopw "
                     "ansible_password=has_sudo_nopw_password"
                     "\n" % (
                distro,
                ci_lib.DOCKER_HOSTNAME,
                BASE_PORT + i,
            ))

    # Build the binaries.
    # run("make -C %s", TESTS_DIR)
    if not ci_lib.exists_in_path('sshpass'):
        run("sudo apt-get update")
        run("sudo apt-get install -y sshpass")


with ci_lib.Fold('ansible'):
    run('/usr/bin/time ./run_ansible_playbook.sh all.yml -i "%s" %s',
        HOSTS_DIR, ' '.join(sys.argv[1:]))
