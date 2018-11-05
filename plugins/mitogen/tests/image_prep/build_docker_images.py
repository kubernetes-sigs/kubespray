#!/usr/bin/env python

"""
Build the Docker images used for testing.
"""

import commands
import os
import tempfile
import shlex
import subprocess


BASEDIR = os.path.dirname(os.path.abspath(__file__))


def sh(s, *args):
    if args:
        s %= args
    return shlex.split(s)



label_by_id = {}

for base_image, label in [
        ('debian:stretch', 'debian'),  # Python 2.7.13, 3.5.3
        ('centos:6', 'centos6'),       # Python 2.6.6
        ('centos:7', 'centos7')        # Python 2.7.5
    ]:
    args = sh('docker run --rm -it -d -h mitogen-%s %s /bin/bash',
              label, base_image)
    container_id = subprocess.check_output(args).strip()
    label_by_id[container_id] = label

with tempfile.NamedTemporaryFile() as fp:
    fp.write('[all]\n')
    for id_, label in label_by_id.items():
        fp.write('%s ansible_host=%s\n' % (label, id_))
    fp.flush()

    try:
        subprocess.check_call(
            cwd=BASEDIR,
            args=sh('ansible-playbook -i %s -c docker setup.yml', fp.name),
        )

        for container_id, label in label_by_id.items():
            subprocess.check_call(sh('''
                docker commit
                --change 'EXPOSE 22'
                --change 'CMD ["/usr/sbin/sshd", "-D"]'
                %s
                mitogen/%s-test
            ''', container_id, label))
    finally:
        subprocess.check_call(sh('docker rm -f %s', ' '.join(label_by_id)))
