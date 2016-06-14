#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Kargo.
#
#    Foobar is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Foobar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
import sys
import hashlib
import urllib2
import yaml
import argparse


def get_remote_sha256_sum(url, max_file_size=100*1024*1024):
    remote = urllib2.urlopen(url)
    hash = hashlib.sha256()
    total_read = 0
    while True:
        data = remote.read(4096)
        total_read += 4096
        if not data or total_read > max_file_size:
            break
        hash.update(data)
    return hash.hexdigest()


def read_vars(var_file):
    """
    Read the variables file
    """
    try:
        with open(var_file, "r") as f:
            kargovars = yaml.load(f)
    except:
        print(
            "Can't read variables file %s" % var_file
        )
        sys.exit(1)
    return kargovars


def get_kube_sha256(version, download_url, binaries):
    kube_sha256 = dict()
    for k in binaries:
        s = get_remote_sha256_sum(download_url + '/' + k)
        kube_sha256[k] = s
        kube_sha256[k + '_checksum'] = kube_sha256.pop(k)
    kube_sha256['kube_apiserver_checksum'] = kube_sha256.pop('kube-apiserver_checksum')
    return(kube_sha256)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='change_k8s_version',
        description='%(prog)s changes the version to be installed with kargo',
    )

    parser.add_argument(
        '-v', '--version', dest='kube_version', required=True,
        help="kubernetes version"
    )
    args = parser.parse_args()

    kube_binaries = ['kubelet', 'kubectl', 'kube-apiserver']
    kargo_root = ".."
    var_files = ['../roles/uploads/defaults/kube_versions.yml', '../roles/download/defaults/kube_versions.yml']
    kube_download_url = "https://storage.googleapis.com/kubernetes-release/release/%s/bin/linux/amd64" % args.kube_version

    new = get_kube_sha256(args.kube_version, kube_download_url, kube_binaries)
    for f in var_files:
        current = read_vars(f)
        current['kube_version'][args.kube_version] = new
        with open(f, 'w') as out:
            out.write(yaml.dump(current, indent=4, default_flow_style=False))
