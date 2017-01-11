# Release Process

The Kargo Project is released on an as-needed basis. The process is as follows:

1. An issue is proposing a new release with a changelog since the last release
2. At least on of the [OWNERS](OWNERS) must LGTM this release
3. An OWNER runs `git tag -s $VERSION` and inserts the changelog and pushes the tag with `git push $VERSION`
4. The release issue is closed
5. An announcement email is sent to `kubernetes-dev@googlegroups.com` with the subject `[ANNOUNCE] kargo $VERSION is released`

## Major/minor releases, merge freezes and milestones

* Kargo does not maintain stable branches for releases. Releases are tags, not
  branches, and there are no backports. Therefore, there is no need for merge
  freezes as well.

* Fixes for major releases (vX.Y.0) are delivered via minor releases (vX.Y.Z)
  and assigned to the corresponding open milestone (vX.Y). That milestone
  remains open for the release support lifetime, which ends once the milestone
  closed. Then only a next major release can be done.

* Kargo major releases are bound to the given ``kube_version`` and other components'
  versions, like etcd or network plugins. Older or newer versions are not
  supported and not tested for the given release.

* Minor releases can change components' versions, but not the ``kube_version``.
  Greater ``kube_version`` requires a new major release.
