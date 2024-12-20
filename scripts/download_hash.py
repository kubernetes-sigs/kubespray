#!/usr/bin/env python3

# After a new version of Kubernetes has been released,
# run this script to update roles/kubespray-defaults/defaults/main/download.yml
# with new hashes.

import sys
import os

from itertools import groupby
from collections import defaultdict
from functools import cache
import argparse
import requests
import hashlib
from ruamel.yaml import YAML
from packaging.version import Version, InvalidVersion

from typing import Optional

CHECKSUMS_YML = "../roles/kubespray-defaults/defaults/main/checksums.yml"

def open_checksums_yaml():
    yaml = YAML()
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = 4096

    with open(CHECKSUMS_YML, "r") as checksums_yml:
        data = yaml.load(checksums_yml)

    return data, yaml

downloads = {
    "calicoctl_binary": {
        'url': "https://github.com/projectcalico/calico/releases/download/v{version}/SHA256SUMS",
        'graphql_id': "R_kgDOA87D0g",
        },
    "ciliumcli_binary": {
        'url': "https://github.com/cilium/cilium-cli/releases/download/v{version}/cilium-{os}-{arch}.tar.gz.sha256sum",
        'graphql_id': "R_kgDOE0nmLg"
        },
    "cni_binary": {
        'url': "https://github.com/containernetworking/plugins/releases/download/v{version}/cni-plugins-{os}-{arch}-v{version}.tgz.sha256",
        'graphql_id': "R_kgDOBQqEpg",
        },
    "containerd_archive": {
        'url': "https://github.com/containerd/containerd/releases/download/v{version}/containerd-{version}-{os}-{arch}.tar.gz.sha256sum",
        'graphql_id': "R_kgDOAr9FWA"
        },
    "crictl": {
        'url': "https://github.com/kubernetes-sigs/cri-tools/releases/download/v{version}/crictl-v{version}-{os}-{arch}.tar.gz.sha256",
        'graphql_id': "R_kgDOBMdURA",
        },
    "crio_archive": {
        'url':"https://storage.googleapis.com/cri-o/artifacts/cri-o.{arch}.v{version}.tar.gz.sha256sum",
        'graphql_id': "R_kgDOBAr5pg",
        },
    "etcd_binary": {
        'url': "https://github.com/etcd-io/etcd/releases/download/v{version}/SHA256SUMS",
        'graphql_id': "R_kgDOAKtHtg",
        },
    "kubeadm": {
        'url': "https://dl.k8s.io/release/v{version}/bin/linux/{arch}/kubeadm.sha256",
        'graphql_id': "R_kgDOAToIkg"
        },
    "kubectl":  {
        'url': "https://dl.k8s.io/release/v{version}/bin/linux/{arch}/kubectl.sha256",
        'graphql_id': "R_kgDOAToIkg"
        },
    "kubelet":  {
        'url': "https://dl.k8s.io/release/v{version}/bin/linux/{arch}/kubelet.sha256",
        'graphql_id': "R_kgDOAToIkg"
        },
    "nerdctl_archive": {
        'url': "https://github.com/containerd/nerdctl/releases/download/v{version}/SHA256SUMS",
        'graphql_id': "R_kgDOEvuRnQ",
        },
    "runc": {
        'url': "https://github.com/opencontainers/runc/releases/download/v{version}/runc.sha256sum",
        'graphql_id': "R_kgDOAjP4QQ",
        },
    "skopeo_binary": {
        'url': "https://github.com/lework/skopeo-binary/releases/download/v{version}/skopeo-{os}-{arch}.sha256",
        'graphql_id': "R_kgDOHQ6J9w",
        },
    "yq": {
        'url':"https://github.com/mikefarah/yq/releases/download/v{version}/checksums-bsd", # see https://github.com/mikefarah/yq/pull/1691 for why we use this url
        'graphql_id': "R_kgDOApOQGQ"
        },
}
# TODO: downloads not supported
# youki: no checkusms in releases
# kata: no checksums in releases
# gvisor: sha512 checksums
# crun : PGP signatures
# cri_dockerd: no checksums or signatures
# helm_archive: PGP signatures
# krew_archive: different yaml structure (in our download)
# calico_crds_archive: different yaml structure (in our download)

# TODO:
# noarch support -> k8s manifests, helm charts
# different checksum format (needs download role changes)
# different verification methods (gpg, cosign) ( needs download role changes) (or verify the sig in this script and only use the checksum in the playbook)
# perf improvements (async)

def download_hash(only_downloads: [str]) -> None:
    # Handle file with multiples hashes, with various formats.
    # the lambda is expected to produce a dictionary of hashes indexed by arch name
    download_hash_extract = {
            "calicoctl_binary": lambda hashes : {
                line.split('-')[-1] : line.split()[0]
                for line in hashes.strip().split('\n')
                if line.count('-') == 2 and line.split('-')[-2] == "linux"
                },
            "etcd_binary": lambda hashes : {
                line.split('-')[-1].removesuffix('.tar.gz') : line.split()[0]
                for line in hashes.strip().split('\n')
                if line.split('-')[-2] == "linux"
                },
             "nerdctl_archive": lambda hashes : {
                line.split()[1].removesuffix('.tar.gz').split('-')[3] : line.split()[0]
                for line in hashes.strip().split('\n')
                if [x for x in line.split(' ') if x][1].split('-')[2] == "linux"
                },
            "runc": lambda hashes : {
                parts[1].split('.')[1] : parts[0]
                for parts in (line.split()
                              for line in hashes.split('\n')[3:9])
                },
             "yq": lambda rhashes_bsd : {
                 pair[0].split('_')[-1] : pair[1]
                 # pair = (yq_<os>_<arch>, <hash>)
                 for pair in ((line.split()[1][1:-1], line.split()[3])
                     for line in rhashes_bsd.splitlines()
                     if line.startswith("SHA256"))
                 if pair[0].startswith("yq")
                     and pair[0].split('_')[1] == "linux"
                     and not pair[0].endswith(".tar.gz")
                },
            }

    data, yaml = open_checksums_yaml()
    s = requests.Session()

    @cache
    def _get_hash_by_arch(download: str, version: str) -> {str: str}:

        hash_file = s.get(downloads[download]['url'].format(
            version = version,
            os = "linux",
            ),
                          allow_redirects=True)
        hash_file.raise_for_status()
        return download_hash_extract[download](hash_file.content.decode())

    nodes_ids = [x['graphql_id'] for x in downloads.values()]
    ql_params = {
            'repoWithReleases': nodes_ids,
            'repoWithTags': [],
    }
    with open("list_releases.graphql") as query:
        response = s.post("https://api.github.com/graphql",
                          json={'query': query.read(), 'variables': ql_params},
                          headers={
                              "Authorization": f"Bearer {os.environ['API_KEY']}",
                              }
                          )
    response.raise_for_status()
    def valid_version(possible_version: str) -> Optional[Version]:
        try:
            return Version(possible_version)
        except InvalidVersion:
            return None

    github_versions = dict(zip(downloads.keys(),
                               [
                                   {
                                       v for r in repo["releases"]["nodes"]
                                       if not r["isPrerelease"]
                                          and (v := valid_version(r["tagName"])) is not None
                                   }
                                   for repo in response.json()["data"]["with_releases"]
                               ],
                               strict=True))

    components_supported_arch = {
            component.removesuffix('_checksums'): [a for a in archs.keys()]
            for component, archs in data.items()
            }
    new_versions = {
            c:
            {v for v in github_versions[c]
                    if any(v > version and (v.major, v.minor) == (version.major, version.minor)
                           for version in [max(minors) for _, minors in groupby(cur_v, lambda v: (v.minor, v.major))])
                           # only get:
                           # - patch versions (no minor or major bump)
                           # - newer ones (don't get old patch version)
            }
            - set(cur_v)
            for component, archs in data.items()
            if (c := component.removesuffix('_checksums')) in downloads.keys()
            # this is only to bound cur_v in the scope
            and (cur_v := sorted(Version(k) for k in next(archs.values().__iter__()).keys()))
        }

    def get_hash(component: str, version: Version, arch: str):
        if component in download_hash_extract:
            hashes = _get_hash_by_arch(component, version)
            return hashes[arch]
        else:
            hash_file = s.get(
                    downloads[component]['url'].format(
                        version = version,
                        os = "linux",
                        arch = arch
                        ),
                    allow_redirects=True)
            hash_file.raise_for_status()
            if downloads[component].get('binary', False):
                return hashlib.sha256(hash_file.content).hexdigest()
            return (hash_file.content.decode().split()[0])


    for component, versions in new_versions.items():
        c = component + '_checksums'
        for arch in components_supported_arch[component]:
            for version in versions:
                data[c][arch][str(version)] = f"{downloads[component].get('hashtype', 'sha256')}:{get_hash(component, version, arch)}"

        data[c] = {arch :
                   {v :
                    versions[v] for v in sorted(versions.keys(),
                                                key=Version,
                                                reverse=True)
                    }
                   for arch, versions in data[c].items()
                   }


    with open(CHECKSUMS_YML, "w") as checksums_yml:
        yaml.dump(data, checksums_yml)
        print(f"\n\nUpdated {CHECKSUMS_YML}\n")

parser = argparse.ArgumentParser(description=f"Add new patch versions hashes in {CHECKSUMS_YML}",
                                 formatter_class=argparse.RawTextHelpFormatter,
                                 epilog=f"""
 This script only lookup new patch versions relative to those already existing
 in the data in {CHECKSUMS_YML},
 which means it won't add new major or minor versions.
 In order to add one of these, edit {CHECKSUMS_YML}
 by hand, adding the new versions with a patch number of 0 (or the lowest relevant patch versions)
 ; then run this script.

 Note that the script will try to add the versions on all
 architecture keys already present for a given download target.

 The '0' value for a version hash is treated as a missing hash, so the script will try to download it again.
 To notify a non-existing version (yanked, or upstream does not have monotonically increasing versions numbers),
 use the special value 'NONE'.

 EXAMPLES:

 crictl_checksums:
      ...
    amd64:
+     v1.30.0: 0
      v1.29.0: d16a1ffb3938f5a19d5c8f45d363bd091ef89c0bc4d44ad16b933eede32fdcbb
      v1.28.0: 8dc78774f7cbeaf787994d386eec663f0a3cf24de1ea4893598096cb39ef2508"""

)
parser.add_argument('binaries', nargs='*', choices=downloads.keys())

args = parser.parse_args()
download_hash(args.binaries)
