# Downloading binaries and containers

The inventory variable `download_delegate` control to which node the download will be delegated.
Any ansible host present in the inventory is a valid value, but there is mainly 3 different mode of operation:

- `download_delegate == {{ inventory_hostname }}`: the node will download itself binaries and container images (this is the current default).
- `download_delegate == localhost`: the Ansible controller will download the binaries and container images for this node.
- `download_delegate == another_host`: The "other node" (`another_host`) will download binaries and images for this node. In that case, there will be an additional step to fetch back the artefacts from the "other node" to localhost.

In all cases, the download and the installation (or for containers, side-loading into the container engine) are separate
steps, which can be done during separate ansible-playbook invocation (with tags, for instance).

Each node can have a different value for `download_delegate`, using inventory variables, but it is recommended to use
the same value for all nodes, in order to delegate downloads to only one node, because this will download each artefact
only once to install it on multiples nodes (for multi architecture cluster, there is one artefact per architecture used
in the cluster).

NOTE: The default is expected to change to `download_delegate` == `localhost` soon.

Container images and binary files are described by the vars like ``foo_version``,
``foo_download_url``, ``foo_checksum`` for binaries and ``foo_image_repo``,
``foo_image_tag`` or optional  ``foo_digest_checksum`` for containers.

Container images may be defined by its repo and tag, for example:
`andyshinn/dnsmasq:2.72`. Or by repo and tag and sha256 digest:
`andyshinn/dnsmasq@sha256:7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193`.

Note, the SHA256 digest and the image tag must be both specified and correspond
to each other. The given example above is represented by the following vars:

```yaml
dnsmasq_digest_checksum: 7c883354f6ea9876d176fe1d30132515478b2859d6fc0cbf9223ffdc09168193
dnsmasq_image_repo: andyshinn/dnsmasq
dnsmasq_image_tag: '2.72'
```

The full list of available vars may be found in the download's ansible role defaults. Those also allow to specify custom urls and local repositories for binaries and container
images as well. See also the DNS stack docs for the related intranet configuration,
so the hosts can resolve those urls and repos.
