# Release Process

The Kubespray Project is released on an as-needed basis. The process is as follows:

1. An issue is proposing a new release with a changelog since the last release. Please see [a good sample issue](https://github.com/kubernetes-sigs/kubespray/issues/8325)
1. At least one of the [approvers](OWNERS_ALIASES) must approve this release
1. (Only for major releases) The `kube_version_min_required` variable is set to `n-1`
1. (Only for major releases) Remove hashes for [EOL versions](https://github.com/kubernetes/website/blob/main/content/en/releases/patch-releases.md) of kubernetes from `*_checksums` variables.
1. Create the release note with [Kubernetes Release Notes Generator](https://github.com/kubernetes/release/blob/master/cmd/release-notes/README.md). See the following `Release note creation` section for the details.
1. An approver creates [new release in GitHub](https://github.com/kubernetes-sigs/kubespray/releases/new) using a version and tag name like `vX.Y.Z` and attaching the release notes
1. (Only for major releases) An approver creates a release branch in the form `release-X.Y`
1. (For major releases) On the `master` branch: bump the version in `galaxy.yml` to the next expected major release (X.y.0 with y = Y + 1), make a Pull Request.
1. (For minor releases) On the `release-X.Y` branch: bump the version in `galaxy.yml` to the next expected minor release (X.Y.z with z = Z + 1), make a Pull Request.
1. The corresponding version of [quay.io/kubespray/kubespray:vX.Y.Z](https://quay.io/repository/kubespray/kubespray) and [quay.io/kubespray/vagrant:vX.Y.Z](https://quay.io/repository/kubespray/vagrant) container images are built and tagged. See the following `Container image creation` section for the details.
1. (Only for major releases) The `KUBESPRAY_VERSION` in `.gitlab-ci.yml` is upgraded to the version we just released # TODO clarify this, this variable is for testing upgrades.
1. The release issue is closed
1. An announcement email is sent to `dev@kubernetes.io` with the subject `[ANNOUNCE] Kubespray $VERSION is released`
1. The topic of the #kubespray channel is updated with `vX.Y.Z is released! | ...`

## Major/minor releases and milestones

* For major releases (vX.Y) Kubespray maintains one branch (`release-X.Y`). Minor releases (vX.Y.Z) are available only as tags.

* Security patches and bugs might be backported.

* Fixes for major releases (vX.Y) and minor releases (vX.Y.Z) are delivered
  via maintenance releases (vX.Y.Z) and assigned to the corresponding open
  [GitHub milestone](https://github.com/kubernetes-sigs/kubespray/milestones).
  That milestone remains open for the major/minor releases support lifetime,
  which ends once the milestone is closed. Then only a next major or minor release
  can be done.

* Kubespray major and minor releases are bound to the given `kube_version` major/minor
  version numbers and other components' arbitrary versions, like etcd or network plugins.
  Older or newer component versions are not supported and not tested for the given
  release (even if included in the checksum variables, like `kubeadm_checksums`).

* There is no unstable releases and no APIs, thus Kubespray doesn't follow
  [semver](https://semver.org/). Every version describes only a stable release.
  Breaking changes, if any introduced by changed defaults or non-contrib ansible roles'
  playbooks, shall be described in the release notes. Other breaking changes, if any in
  the contributed addons or bound versions of Kubernetes and other components, are
  considered out of Kubespray scope and are up to the components' teams to deal with and
  document.

* Minor releases can change components' versions, but not the major `kube_version`.
  Greater `kube_version` requires a new major or minor release. For example, if Kubespray v2.0.0
  is bound to `kube_version: 1.4.x`, `calico_version: 0.22.0`, `etcd_version: v3.0.6`,
  then Kubespray v2.1.0 may be bound to only minor changes to `kube_version`, like v1.5.1
  and *any* changes to other components, like etcd v4, or calico 1.2.3.
  And Kubespray v3.x.x shall be bound to `kube_version: 2.x.x` respectively.

## Release note creation

You can create a release note with:

```shell
export GITHUB_TOKEN=<your-github-token>
export ORG=kubernetes-sigs
export REPO=kubespray
release-notes --start-sha <The start commit-id> --end-sha <The end commit-id> --dependencies=false --output=/tmp/kubespray-release-note --required-author=""
```

If the release note file(/tmp/kubespray-release-note) contains "### Uncategorized" pull requests, those pull requests don't have a valid kind label(`kind/feature`, etc.).
It is necessary to put a valid label on each pull request and run the above release-notes command again to get a better release note

## Container image creation

The container image `quay.io/kubespray/kubespray:vX.Y.Z` can be created from Dockerfile of the kubespray root directory:

```shell
cd kubespray/
nerdctl build -t quay.io/kubespray/kubespray:vX.Y.Z .
nerdctl push quay.io/kubespray/kubespray:vX.Y.Z
```

The container image `quay.io/kubespray/vagrant:vX.Y.Z` can be created from build.sh of test-infra/vagrant-docker/:

```shell
cd kubespray/test-infra/vagrant-docker/
./build vX.Y.Z
```

Please note that the above operation requires the permission to push container images into quay.io/kubespray/.
If you don't have the permission, please ask it on the #kubespray-dev channel.
