# Warning

This directory is full of disorganized crap, including random hacks I checked
in that I'd like to turn into tests. The effort to write tests only really
started in September 2017. Pull requests in this area are very welcome!


## Running The Tests

[![Build Status](https://api.travis-ci.org/dw/mitogen.svg?branch=master)](https://travis-ci.org/dw/mitogen)

Your computer should have an Internet connection, and the ``docker`` command
line tool should be able to connect to a working Docker daemon (localhost or
elsewhere for OS X etc.) that can run new images.

The IP address of the Docker daemon must allow exposing ports from running
containers, e.g. it should not be firewalled or port forwarded.

If in doubt, just install Docker on a Linux box in the default configuration
and run the tests there.

## Steps To Prepare Development Environment

1. Get the code ``git clone https://github.com/dw/mitogen.git``
1. Go into the working directory ``cd mitogen``
1. Establish the docker image ``./tests/build_docker_image.py``
1. Build the virtual environment ``virtualenv ../venv``
1. Enable the virtual environment we just built ``source ../venv/bin/activate``
1. Install Mitogen in pip editable mode ``pip install -e .``
1. Run ``test``


# Selecting a target distribution

Docker target images exist for testing against CentOS and Debian, with the
default being Debian. To select CentOS, specify `MITOGEN_TEST_DISTRO=centos` in
the environment.


# User Accounts

A set of standard user account names are used by in the Docker container and
also by Ansible's `osx_setup.yml`.

`root`
    In the Docker image only, the password is "rootpassword".

`mitogen__has_sudo`
    The login password is "has_sudo_password" and the account is capable of
    sudoing to root, by supplying the account password to sudo.

`mitogen__has_sudo_pubkey`
    The login password is "has_sudo_pubkey_password". Additionally
    `tests/data/docker/mitogen__has_sudo_pubkey.key` SSH key may be used to log
    in. It can sudo the same as `mitogen__has_sudo`.

`mitogen__has_sudo_nopw`
    The login password is "has_sudo_nopw_password". It can sudo to root without
    supplying a password. It has explicit sudoers rules forcing it to require a
    password for other accounts.

`mitogen__pw_required`
    The login password is "pw_required_password". When "sudo -u" is used to
    target this account, its password must be entered rather than the login
    user's password.

`mitogen__require_tty`
    The login password is "require_tty_password". When "sudo -u" is used to
    target this account, the parent session requires a TTY.

`mitogen__require_tty_pw_required`
    The login password is "require_tty_pw_required_password". When "sudo -u" is
    used to target this account, the parent session requires a TTY and the
    account password must be entered.

`mitogen__user1` .. `mitogen__user5`
    These accounts do not have passwords set. They exist to test the Ansible
    interpreter recycling logic.

`mitogen__sudo1` .. `mitogen__sudo4`
    May passwordless sudo to any account.

`mitogen__webapp`
    A plain old account with no sudo access, used as the target for fakessh
    tests.


# Ansible Integration Test Environment

The integration tests expect to be run against a either one of the Docker
images, or a similar target with the same set of UNIX accounts and sudo rules.

The login account should be able to sudo to root witout a password.
