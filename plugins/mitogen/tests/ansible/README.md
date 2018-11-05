
# `tests/ansible` Directory

This is an an organically growing collection of integration and regression
tests used for development and end-user bug reports.

It will be tidied up over time, meanwhile, the playbooks here are a useful
demonstrator for what does and doesn't work.


## Preparation

See `../image_prep/README.md`.


## `run_ansible_playbook.sh`

This is necessary to set some environment variables used by future tests, as
there appears to be no better way to inject them into the top-level process
environment before the Mitogen connection process forks.


## Running Everything

`ANSIBLE_STRATEGY=mitogen_linear ./run_ansible_playbook.sh all.yml`


## `hosts/` and `common-hosts`

To support running the tests against a dev machine that has the requisite user
accounts, the the default inventory is a directory containing a 'localhost'
file that defines 'localhost' to be named 'target' in Ansible inventory, and a
symlink to 'common-hosts', which defines additional targets that all derive
from 'target'.

This allows `ansible_tests.sh` to reuse the common-hosts definitions while
replacing localhost as the test target by creating a new directory that
similarly symlinks in common-hosts.

There may be a better solution for this, but it works fine for now.
