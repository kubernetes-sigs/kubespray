#!/usr/bin/env python3

# After a new version of Kubernetes has been released,
# run this script to update roles/kubespray_defaults/defaults/main/download.yml
# with new hashes.

import sys
import os
import logging
import subprocess

from itertools import groupby, chain
from more_itertools import partition
from functools import cache
import argparse
import requests
import hashlib
from datetime import datetime
from ruamel.yaml import YAML
from packaging.version import Version, InvalidVersion
from importlib.resources import files
from pathlib import Path

from typing import Optional, Any

from . import components

CHECKSUMS_YML = Path("roles/kubespray_defaults/vars/main/checksums.yml")

logger = logging.getLogger(__name__)


def open_yaml(file: Path):
    yaml = YAML()
    yaml.explicit_start = True
    yaml.preserve_quotes = True
    yaml.width = 4096

    with open(file, "r") as checksums_yml:
        data = yaml.load(checksums_yml)

    return data, yaml


arch_alt_name = {
    "amd64": "x86_64",
    "arm64": "aarch64",
    "ppc64le": None,
    "arm": None,
    "no_arch": None,
}

# TODO: downloads not supported
# helm_archive: PGP signatures

# TODO:
# different verification methods (gpg, cosign) ( needs download role changes) (or verify the sig in this script and only use the checksum in the playbook)
# perf improvements (async)


def download_hash(downloads: {str: {str: Any}}) -> None:
    # Handle file with multiples hashes, with various formats.
    # the lambda is expected to produce a dictionary of hashes indexed by arch name
    download_hash_extract = {
        "calicoctl_binary": lambda hashes: {
            line.split("-")[-1]: line.split()[0]
            for line in hashes.strip().split("\n")
            if line.count("-") == 2 and line.split("-")[-2] == "linux"
        },
        "etcd_binary": lambda hashes: {
            line.split("-")[-1].removesuffix(".tar.gz"): line.split()[0]
            for line in hashes.strip().split("\n")
            if line.split("-")[-2] == "linux"
        },
        "nerdctl_archive": lambda hashes: {
            line.split()[1].removesuffix(".tar.gz").split("-")[3]: line.split()[0]
            for line in hashes.strip().split("\n")
            if [x for x in line.split(" ") if x][1].split("-")[2] == "linux"
        },
        "runc": lambda hashes: {
            parts[1].split(".")[1]: parts[0]
            for parts in (line.split() for line in hashes.split("\n")[3:9])
        },
        "yq": lambda rhashes_bsd: {
            pair[0].split("_")[-1]: pair[1]
            # pair = (yq_<os>_<arch>, <hash>)
            for pair in (
                (line.split()[1][1:-1], line.split()[3])
                for line in rhashes_bsd.splitlines()
                if line.startswith("SHA256")
            )
            if pair[0].startswith("yq")
            and pair[0].split("_")[1] == "linux"
            and not pair[0].endswith(".tar.gz")
        },
    }

    checksums_file = (
        Path(
            subprocess.Popen(
                ["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE
            )
            .communicate()[0]
            .rstrip()
            .decode("utf-8")
        )
        / CHECKSUMS_YML
    )
    logger.info("Opening checksums file %s...", checksums_file)
    data, yaml = open_yaml(checksums_file)
    s = requests.Session()

    @cache
    def _get_hash_by_arch(download: str, version: str) -> {str: str}:

        hash_file = s.get(
            downloads[download]["url"].format(
                version=version,
                os="linux",
            ),
            allow_redirects=True,
        )
        hash_file.raise_for_status()
        return download_hash_extract[download](hash_file.content.decode())

    releases, tags = map(
        dict, partition(lambda r: r[1].get("tags", False), downloads.items())
    )
    repos = {
        "with_releases": [r["graphql_id"] for r in releases.values()],
        "with_tags": [t["graphql_id"] for t in tags.values()],
    }
    response = s.post(
        "https://api.github.com/graphql",
        json={
            "query": files(__package__).joinpath("list_releases.graphql").read_text(),
            "variables": repos,
        },
        headers={
            "Authorization": f"Bearer {os.environ['API_KEY']}",
        },
    )
    if "x-ratelimit-used" in response.headers._store:
        logger.info(
            "Github graphQL API ratelimit status: used %s of %s. Next reset at %s",
            response.headers["X-RateLimit-Used"],
            response.headers["X-RateLimit-Limit"],
            datetime.fromtimestamp(int(response.headers["X-RateLimit-Reset"])),
        )
    response.raise_for_status()

    def valid_version(possible_version: str) -> Optional[Version]:
        try:
            return Version(possible_version)
        except InvalidVersion:
            return None

    repos = response.json()["data"]
    github_versions = dict(
        zip(
            chain(releases.keys(), tags.keys()),
            [
                {
                    v
                    for r in repo["releases"]["nodes"]
                    if not r["isPrerelease"]
                    and (v := valid_version(r["tagName"])) is not None
                }
                for repo in repos["with_releases"]
            ]
            + [
                {
                    v
                    for t in repo["refs"]["nodes"]
                    if (v := valid_version(t["name"].removeprefix("release-")))
                    is not None
                }
                for repo in repos["with_tags"]
            ],
            strict=True,
        )
    )

    components_supported_arch = {
        component.removesuffix("_checksums"): [a for a in archs.keys()]
        for component, archs in data.items()
    }
    new_versions = {
        c: {
            v
            for v in github_versions[c]
            if any(
                v > version
                and (
                    (v.major, v.minor) == (version.major, version.minor)
                    or c.startswith("gvisor")
                )
                for version in [
                    max(minors)
                    for _, minors in groupby(cur_v, lambda v: (v.minor, v.major))
                ]
            )
            # only get:
            # - patch versions (no minor or major bump) (exception for gvisor which does not have a major.minor.patch scheme
            # - newer ones (don't get old patch version)
        }
        - set(cur_v)
        for component, archs in data.items()
        if (c := component.removesuffix("_checksums")) in downloads.keys()
        # this is only to bound cur_v in the scope
        and (
            cur_v := sorted(
                Version(str(k)) for k in next(archs.values().__iter__()).keys()
            )
        )
    }

    hash_set_to_0 = {
        c: {
            Version(str(v))
            for v, h in chain.from_iterable(a.items() for a in archs.values())
            if h == 0
        }
        for component, archs in data.items()
        if (c := component.removesuffix("_checksums")) in downloads.keys()
    }

    def get_hash(component: str, version: Version, arch: str):
        if component in download_hash_extract:
            hashes = _get_hash_by_arch(component, version)
            return hashes[arch]
        else:
            hash_file = s.get(
                downloads[component]["url"].format(
                    version=version,
                    os="linux",
                    arch=arch,
                    alt_arch=arch_alt_name[arch],
                ),
                allow_redirects=True,
            )
            hash_file.raise_for_status()
            if downloads[component].get("binary", False):
                return hashlib.new(
                    downloads[component].get("hashtype", "sha256"), hash_file.content
                ).hexdigest()
            return hash_file.content.decode().split()[0]

    for component, versions in chain(new_versions.items(), hash_set_to_0.items()):
        c = component + "_checksums"
        for arch in components_supported_arch[component]:
            for version in versions:
                data[c][arch][
                    str(version)
                ] = f"{downloads[component].get('hashtype', 'sha256')}:{get_hash(component, version, arch)}"

        data[c] = {
            arch: {
                v: versions[v]
                for v in sorted(
                    versions.keys(), key=lambda v: Version(str(v)), reverse=True
                )
            }
            for arch, versions in data[c].items()
        }

    with open(checksums_file, "w") as checksums_yml:
        yaml.dump(data, checksums_yml)
    logger.info("Updated %s", checksums_file)


def main():

    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    parser = argparse.ArgumentParser(
        description=f"Add new patch versions hashes in {CHECKSUMS_YML}",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=f"""
     This script only lookup new patch versions relative to those already existing
     in the data in {CHECKSUMS_YML},
     which means it won't add new major or minor versions.
     In order to add one of these, edit {CHECKSUMS_YML}
     by hand, adding the new versions with a patch number of 0 (or the lowest relevant patch versions)
     and a hash value of 0.
     ; then run this script.

     Note that the script will try to add the versions on all
     architecture keys already present for a given download target.

     EXAMPLES:

     crictl_checksums:
          ...
        amd64:
    +     1.30.0: 0
          1.29.0: d16a1ffb3938f5a19d5c8f45d363bd091ef89c0bc4d44ad16b933eede32fdcbb
          1.28.0: 8dc78774f7cbeaf787994d386eec663f0a3cf24de1ea4893598096cb39ef2508""",
    )

    # Workaround for https://github.com/python/cpython/issues/53834#issuecomment-2060825835
    # Fixed in python 3.14
    class Choices(tuple):

        def __init__(self, _iterable=None, default=None):
            self.default = default or []

        def __contains__(self, item):
            return super().__contains__(item) or item == self.default

    choices = Choices(components.infos.keys(), default=list(components.infos.keys()))

    parser.add_argument(
        "only",
        nargs="*",
        choices=choices,
        help="if provided, only obtain hashes for these compoments",
        default=choices.default,
    )
    parser.add_argument(
        "-e",
        "--exclude",
        action="append",
        choices=components.infos.keys(),
        help="do not obtain hashes for this component",
        default=[],
    )

    args = parser.parse_args()
    download_hash(
        {k: components.infos[k] for k in (set(args.only) - set(args.exclude))}
    )
