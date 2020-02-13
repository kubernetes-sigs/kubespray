# Release Process

The Kubespray Project is released on an as-needed basis. The process is as follows:

1. An issue is proposing a new release with a changelog since the last release
2. At least one of the [approvers](OWNERS_ALIASES) must approve this release
3. An approver creates [new release in GitHub](https://github.com/kubernetes-sigs/kubespray/releases/new) using a version and tag name like `vX.Y.Z` and attaching the release notes
4. An approver creates a release branch in the form `release-X.Y`
5. The corresponding version of [quay.io/kubespray/kubespray:vX.Y.Z](https://quay.io/repository/kubespray/kubespray) docker image is built and tagged
6. The `KUBESPRAY_VERSION` variable is updated in `.gitlab-ci.yml`
7. The release issue is closed
8. An announcement email is sent to `kubernetes-dev@googlegroups.com` with the subject `[ANNOUNCE] Kubespray $VERSION is released`
9. The topic of the #kubespray channel is updated with `vX.Y.Z is released! | ...`

## Major/minor releases, merge freezes and milestones

* Kubespray maintains one branch for major releases (vX.Y). Minor releases are available only as tags.

* Security patches and bugs might be backported.

* Fixes for major releases (vX.x.0) and minor releases (vX.Y.x) are delivered
  via maintenance releases (vX.Y.Z) and assigned to the corresponding open
  milestone (vX.Y). That milestone remains open for the major/minor releases
  support lifetime, which ends once the milestone closed. Then only a next major
  or minor release can be done.

* Kubespray major and minor releases are bound to the given ``kube_version`` major/minor
  version numbers and other components' arbitrary versions, like etcd or network plugins.
  Older or newer versions are not supported and not tested for the given release.

* There is no unstable releases and no APIs, thus Kubespray doesn't follow
  [semver](https://semver.org/). Every version describes only a stable release.
  Breaking changes, if any introduced by changed defaults or non-contrib ansible roles'
  playbooks, shall be described in the release notes. Other breaking changes, if any in
  the contributed addons or bound versions of Kubernetes and other components, are
  considered out of Kubespray scope and are up to the components' teams to deal with and
  document.

* Minor releases can change components' versions, but not the major ``kube_version``.
  Greater ``kube_version`` requires a new major or minor release. For example, if Kubespray v2.0.0
  is bound to ``kube_version: 1.4.x``, ``calico_version: 0.22.0``, ``etcd_version: v3.0.6``,
  then Kubespray v2.1.0 may be bound to only minor changes to ``kube_version``, like v1.5.1
  and *any* changes to other components, like etcd v4, or calico 1.2.3.
  And Kubespray v3.x.x shall be bound to ``kube_version: 2.x.x`` respectively.
