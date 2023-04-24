# Contributing guidelines

## How to become a contributor and submit your own code

### Environment setup

It is recommended to use filter to manage the GitHub email notification, see [examples for setting filters to Kubernetes Github notifications](https://github.com/kubernetes/community/blob/master/communication/best-practices.md#examples-for-setting-filters-to-kubernetes-github-notifications)

To install development dependencies you can set up a python virtual env with the necessary dependencies:

```ShellSession
virtualenv venv
source venv/bin/activate
pip install -r tests/requirements.txt
ansible-galaxy install -r tests/requirements.yml
```

#### Linting

Kubespray uses [pre-commit](https://pre-commit.com) hook configuration to run several linters, please install this tool and use it to run validation tests before submitting a PR.

```ShellSession
pre-commit install
pre-commit run -a  # To run pre-commit hook on all files in the repository, even if they were not modified
```

#### Molecule

[molecule](https://github.com/ansible-community/molecule) is designed to help the development and testing of Ansible roles. In Kubespray you can run it all for all roles with `./tests/scripts/molecule_run.sh` or for a specific role (that you are working with) with `molecule test` from the role directory (`cd roles/my-role`).

When developing or debugging a role it can be useful to run `molecule create` and `molecule converge` separately. Then you can use `molecule login` to SSH into the test environment.

#### Vagrant

Vagrant with VirtualBox or libvirt driver helps you to quickly spin test clusters to test things end to end. See [README.md#vagrant](README.md)

### Contributing A Patch

1. Submit an issue describing your proposed change to the repo in question.
2. The [repo owners](OWNERS) will respond to your issue promptly.
3. Fork the desired repo, develop and test your code changes.
4. Install [pre-commit](https://pre-commit.com) and install it in your development repo.
5. Addess any pre-commit validation failures.
6. Sign the CNCF CLA (<https://git.k8s.io/community/CLA.md#the-contributor-license-agreement>)
7. Submit a pull request.
8. Work with the reviewers on their suggestions.
9. Ensure to rebase to the HEAD of your target branch and squash un-necessary commits (<https://blog.carbonfive.com/always-squash-and-rebase-your-git-commits/>) before final merger of your contribution.
