"""
Static download metadata for components updated by the update-hashes command.
"""

infos = {
    "calicoctl_binary": {
        "url": "https://github.com/projectcalico/calico/releases/download/v{version}/SHA256SUMS",
        "graphql_id": "R_kgDOA87D0g",
    },
    "calico_crds_archive": {
        "url": "https://github.com/projectcalico/calico/archive/v{version}.tar.gz",
        "graphql_id": "R_kgDOA87D0g",
        "binary": True,
    },
    "ciliumcli_binary": {
        "url": "https://github.com/cilium/cilium-cli/releases/download/v{version}/cilium-{os}-{arch}.tar.gz.sha256sum",
        "graphql_id": "R_kgDOE0nmLg",
    },
    "cni_binary": {
        "url": "https://github.com/containernetworking/plugins/releases/download/v{version}/cni-plugins-{os}-{arch}-v{version}.tgz.sha256",
        "graphql_id": "R_kgDOBQqEpg",
    },
    "containerd_archive": {
        "url": "https://github.com/containerd/containerd/releases/download/v{version}/containerd-{version}-{os}-{arch}.tar.gz.sha256sum",
        "graphql_id": "R_kgDOAr9FWA",
    },
    "containerd_static_archive": {
        "url": "https://github.com/containerd/containerd/releases/download/v{version}/containerd-static-{version}-{os}-{arch}.tar.gz.sha256sum",
        "graphql_id": "R_kgDOAr9FWA",
    },
    "cri_dockerd_archive": {
        "binary": True,
        "url": "https://github.com/Mirantis/cri-dockerd/releases/download/v{version}/cri-dockerd-{version}.{arch}.tgz",
        "graphql_id": "R_kgDOEvvLcQ",
    },
    "crictl": {
        "url": "https://github.com/kubernetes-sigs/cri-tools/releases/download/v{version}/crictl-v{version}-{os}-{arch}.tar.gz.sha256",
        "graphql_id": "R_kgDOBMdURA",
    },
    "crio_archive": {
        "url": "https://storage.googleapis.com/cri-o/artifacts/cri-o.{arch}.v{version}.tar.gz.sha256sum",
        "graphql_id": "R_kgDOBAr5pg",
    },
    "crun": {
        "url": "https://github.com/containers/crun/releases/download/{version}/crun-{version}-linux-{arch}",
        "binary": True,
        "graphql_id": "R_kgDOBip3vA",
    },
    "etcd_binary": {
        "url": "https://github.com/etcd-io/etcd/releases/download/v{version}/SHA256SUMS",
        "graphql_id": "R_kgDOAKtHtg",
    },
    "gvisor_containerd_shim_binary": {
        "url": "https://storage.googleapis.com/gvisor/releases/release/{version}/{alt_arch}/containerd-shim-runsc-v1.sha512",
        "hashtype": "sha512",
        "tags": True,
        "graphql_id": "R_kgDOB9IlXg",
    },
    "gvisor_runsc_binary": {
        "url": "https://storage.googleapis.com/gvisor/releases/release/{version}/{alt_arch}/runsc.sha512",
        "hashtype": "sha512",
        "tags": True,
        "graphql_id": "R_kgDOB9IlXg",
    },
    "kata_containers_binary": {
        "url": "https://github.com/kata-containers/kata-containers/releases/download/{version}/kata-static-{version}-{arch}.tar.xz",
        "binary": True,
        "graphql_id": "R_kgDOBsJsHQ",
    },
    "kubeadm": {
        "url": "https://dl.k8s.io/release/v{version}/bin/linux/{arch}/kubeadm.sha256",
        "graphql_id": "R_kgDOAToIkg",
    },
    "kubectl": {
        "url": "https://dl.k8s.io/release/v{version}/bin/linux/{arch}/kubectl.sha256",
        "graphql_id": "R_kgDOAToIkg",
    },
    "kubelet": {
        "url": "https://dl.k8s.io/release/v{version}/bin/linux/{arch}/kubelet.sha256",
        "graphql_id": "R_kgDOAToIkg",
    },
    "nerdctl_archive": {
        "url": "https://github.com/containerd/nerdctl/releases/download/v{version}/SHA256SUMS",
        "graphql_id": "R_kgDOEvuRnQ",
    },
    "runc": {
        "url": "https://github.com/opencontainers/runc/releases/download/v{version}/runc.sha256sum",
        "graphql_id": "R_kgDOAjP4QQ",
    },
    "skopeo_binary": {
        "url": "https://github.com/lework/skopeo-binary/releases/download/v{version}/skopeo-{os}-{arch}.sha256",
        "graphql_id": "R_kgDOHQ6J9w",
    },
    "youki": {
        "url": "https://github.com/youki-dev/youki/releases/download/v{version}/youki-{version}-{alt_arch}-gnu.tar.gz",
        "binary": True,
        "graphql_id": "R_kgDOFPvgPg",
    },
    "yq": {
        "url": "https://github.com/mikefarah/yq/releases/download/v{version}/checksums-bsd",  # see https://github.com/mikefarah/yq/pull/1691 for why we use this url
        "graphql_id": "R_kgDOApOQGQ",
    },
    "argocd_install": {
        "url": "https://raw.githubusercontent.com/argoproj/argo-cd/v{version}/manifests/install.yaml",
        "graphql_id": "R_kgDOBzS60g",
        "binary": True,
        "hashtype": "sha256",
    },
    "gateway_api_standard_crds": {
        "url": "https://github.com/kubernetes-sigs/gateway-api/releases/download/v{version}/standard-install.yaml",
        "graphql_id": "R_kgDODQ6RZw",
        "binary": True,
    },
    "gateway_api_experimental_crds": {
        "url": "https://github.com/kubernetes-sigs/gateway-api/releases/download/v{version}/experimental-install.yaml",
        "graphql_id": "R_kgDODQ6RZw",
        "binary": True,
    },
}
