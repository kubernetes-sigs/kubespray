#!/usr/bin/env python

import difflib
import logging
import re
import subprocess
import tempfile

LOG = logging.getLogger(__name__)

suffixes = [
    '-m custom_bash_old_style_module',
    '-m custom_bash_want_json_module',
    '-m custom_binary_producing_json',
    '-m custom_binary_producing_junk',
    '-m custom_binary_single_null',
    '-m custom_python_json_args_module',
    '-m custom_python_new_style_module',
    '-m custom_python_want_json_module',
    '-m setup',
]

fixups = [
    ('Shared connection to localhost closed\\.(\r\n)?', ''),  # TODO
]


def fixup(s):
    for regex, to in fixups:
        s = re.sub(regex, to, s, re.DOTALL|re.M)
    return s


def run(s):
    LOG.debug('running: %r', s)
    with tempfile.NamedTemporaryFile() as fp:
        # https://www.systutorials.com/docs/linux/man/1-ansible-playbook/#lbAG
        returncode = subprocess.call(s, stdout=fp, stderr=fp, shell=True)
        fp.write('\nReturn code: %s\n' % (returncode,))
        fp.seek(0)
        return fp.read()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    for suffix in suffixes:
        ansible = run('ansible localhost %s' % (suffix,))
        mitogen = run('ANSIBLE_STRATEGY=mitogen ansible localhost %s' % (suffix,))

        diff = list(difflib.unified_diff(
            a=fixup(ansible).splitlines(),
            b=fixup(mitogen).splitlines(),
            fromfile='ansible-output.txt',
            tofile='mitogen-output.txt',
        ))
        if diff:
            print('++ differ! suffix: %r' % (suffix,))
            for line in diff:
                print(line)
            print
            print
