# gitlab-branch-cleanup

Cleanup old branches in a GitLab project

## Installation

```shell
pip install -r requirements.txt
python main.py --help
```

## Usage

```console
$ export GITLAB_API_TOKEN=foobar
$ python main.py kargo-ci/kubernetes-sigs-kubespray
Deleting branch pr-5220-containerd-systemd from 2020-02-17 ...
Deleting branch pr-5561-feature/cinder_csi_fixes from 2020-02-17 ...
Deleting branch pr-5607-add-flatcar from 2020-02-17 ...
Deleting branch pr-5616-fix-typo from 2020-02-17 ...
Deleting branch pr-5634-helm_310 from 2020-02-18 ...
Deleting branch pr-5644-patch-1 from 2020-02-15 ...
Deleting branch pr-5647-master from 2020-02-17 ...
```
