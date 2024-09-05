#!/usr/bin/env python3

# After a new version of Kubernetes has been released,
# run this script to update roles/kubespray-defaults/defaults/main/download.yml
# with new hashes.

import sys

from itertools import count, groupby
from collections import defaultdict
import argparse
import requests
from ruamel.yaml import YAML
from packaging.version import Version

CHECKSUMS_YML = "../roles/kubespray-defaults/defaults/main/checksums.yml"

def open_checksums_yaml():
    yaml = YAML()
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = 4096

    with open(CHECKSUMS_YML, "r") as checksums_yml:
        data = yaml.load(checksums_yml)

    return data, yaml

def version_compare(version):
    return Version(version.removeprefix("v"))

downloads = {
    "containerd_archive": "https://github.com/containerd/containerd/releases/download/v{version}/containerd-{version}-{os}-{arch}.tar.gz.sha256sum",
    "kubeadm": "https://dl.k8s.io/release/{version}/bin/linux/{arch}/kubeadm.sha256",
    "kubectl": "https://dl.k8s.io/release/{version}/bin/linux/{arch}/kubectl.sha256",
    "kubelet": "https://dl.k8s.io/release/{version}/bin/linux/{arch}/kubelet.sha256",
    "runc": "https://github.com/opencontainers/runc/releases/download/{version}/runc.sha256sum",
}

def download_hash(only_downloads: [str]) -> None:
    # Handle hashes not directly in one url per hash. Return dict of hashs indexed by arch
    download_hash_extract = {
            "runc": lambda hashes : {
                parts[1].split('.')[1] : parts[0]
                for parts in (line.split()
                              for line in hashes.split('\n')[3:9])
                },
            }

    data, yaml = open_checksums_yaml()

    for download, url in (downloads if only_downloads == []
                          else {k:downloads[k] for k in downloads.keys() & only_downloads}).items():
        checksum_name = f"{download}_checksums"
        for arch, versions in data[checksum_name].items():
            for minor, patches in groupby(versions.copy().keys(), lambda v : '.'.join(v.split('.')[:-1])):
                for version in (f"{minor}.{patch}" for patch in
                                count(start=int(max(patches, key=version_compare).split('.')[-1]),
                                      step=1)):
                    # Those barbaric generators do the following:
                    # Group all patches versions by minor number, take the newest and start from that
                    # to find new versions
                    if version in versions and versions[version] != 0:
                        continue
                    hash_file = requests.get(downloads[download].format(
                        version = version,
                        os = "linux",
                        arch = arch
                        ),
                     allow_redirects=True)
                    if hash_file.status_code == 404:
                        print(f"Unable to find {download} hash file for version {version} (arch: {arch}) at {hash_file.url}")
                        break
                    hash_file.raise_for_status()
                    sha256sum = hash_file.content.decode()
                    if download in download_hash_extract:
                        sha256sum = download_hash_extract[download](sha256sum).get(arch)
                        if sha256sum == None:
                            break
                    sha256sum = sha256sum.split()[0]

                    if len(sha256sum) != 64:
                        raise Exception(f"Checksum has an unexpected length: {len(sha256sum)} (binary: {download}, arch: {arch}, release: {version}, checksum: '{sha256sum}')")
                    data[checksum_name][arch][version] = sha256sum
        data[checksum_name] = {arch : {r : releases[r] for r in sorted(releases.keys(),
                                                  key=version_compare,
                                                  reverse=True)}
                               for arch, releases in data[checksum_name].items()}

    with open(CHECKSUMS_YML, "w") as checksums_yml:
        yaml.dump(data, checksums_yml)
        print(f"\n\nUpdated {CHECKSUMS_YML}\n")

parser = argparse.ArgumentParser(description=f"Add new patch versions hashes in {CHECKSUMS_YML}")
parser.add_argument('binaries', nargs='*', choices=downloads.keys())

args = parser.parse_args()
download_hash(args.binaries)
