#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 Kubespray
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import hashlib
import urllib2
import yaml
import argparse
import shutil
from re import sub


def get_remote_sha256_sum(url, max_file_size=1024*1024*1024):
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
    kube_sha256['kube_apiserver'] = kube_sha256.pop('kube-apiserver')
    return(kube_sha256)


def file_sub(file, regex, string):
    "Substitute string in a file"
    shutil.move(file, file + '~')
    f = open(file + '~', 'r')
    data = f.read()
    o = open(file, 'w')
    o.write(sub(regex, string, data))
    f.close()
    o.close()
    os.remove(file + '~')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='change_k8s_version',
        description='%(prog)s changes the version to be installed with kargo',
    )

    parser.add_argument(
        '-v', '--version', dest='kube_version', required=True,
        help="kubernetes version"
    )
    parser.add_argument(
        '-r', '--repository', dest='docker_repository', required=True,
        help="hyperkube docker repository"
    )
    args = parser.parse_args()

    kargo_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    file_sub(
        os.path.join(kargo_root_path, 'roles/kubernetes/node/defaults/main.yml'),
        r'.*hyperkube_image_repo.*', 'hyperkube_image_repo: "%s"' % args.docker_repository
    )
    file_sub(
        os.path.join(kargo_root_path, 'roles/kubernetes/node/defaults/main.yml'),
        r'.*hyperkube_image_tag.*', 'hyperkube_image_tag: "%s"' % args.kube_version
    )

    kube_binaries = ['kubelet', 'kubectl', 'kube-apiserver']
    var_files = [
        os.path.join(kargo_root_path, 'roles/uploads/vars/kube_versions.yml'),
        os.path.join(kargo_root_path, 'roles/download/vars/kube_versions.yml')
    ]
    kube_download_url = "https://storage.googleapis.com/kubernetes-release/release/%s/bin/linux/amd64" % args.kube_version

    new = get_kube_sha256(args.kube_version, kube_download_url, kube_binaries)
    for f in var_files:
        current = read_vars(f)
        current['kube_checksum'][args.kube_version] = new
        current['kube_version'] = args.kube_version
        with open(f, 'w') as out:
            out.write(yaml.dump(current, indent=4, default_flow_style=False))
