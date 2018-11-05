
# `image_prep`

This directory contains Ansible playbooks for building the Docker containers
used for testing, or for setting up an OS X laptop so the tests can (mostly)
run locally.

The Docker config is more heavily jinxed to trigger adverse conditions in the
code, the OS X config just has the user accounts.

See ../README.md for a (mostly) description of the accounts created.


## Building the containers

``./build_docker_images.sh``


## Preparing an OS X box

WARNING: this creates a ton of accounts with preconfigured passwords. It is
generally impossible to restrict remote access to these, so your only option is
to disable remote login and sharing.

``ansible-playbook -b -c local -i localhost, -l localhost setup.yml``
