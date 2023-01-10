#!/usr/bin/env python3

import os
import re
import shutil
import time
from subprocess import PIPE, run

TOTAL_UPLOAD = int(os.getenv("MAX_UPLOAD", 600))
threshold = float(os.getenv("UPLOADER_THRESHOLD", 0.7))
local_path = os.getenv("BACKUP_PATH", "/media")
remote_path = os.getenv("RCLONE_REMOTE", "myfakeremote:/myfakepath/media")

def rclone(*args):
    rclone_config = "/tmp/rclone.conf"
    if not os.path.exists(rclone_config):
        shutil.copyfile(
            os.getenv("RCLONE_CONFIG_PATH", "/myrclone_config_path/rclone.conf"),
            rclone_config,
        )

    return (
        run(
            [
                "rclone",
                "--config",
                rclone_config,
                *args,
            ],
            stdout=PIPE,
        )
        .stdout.decode("utf8")
        .split("\n")
    )


def get_usage():
    stat = shutil.disk_usage(local_path)
    return stat.used / stat.total * 1.1


def get_size(fname):
    return os.path.getsize(fname) / (1024.0 * 1024 * 1024)


# get a list of files that exist on the remote
remote_files = []
for line in rclone("ls", remote_path):
    line = re.sub(r"^\d+\s+", "", line.strip()).strip()
    fname = os.path.join(local_path, line)
    remote_files.append(fname)

# upload
to_delete = []
for root, dirs, files in os.walk(local_path):
    for f in files:
        fname = os.path.join(root, f)
        size = get_size(fname)
        remote_fname = os.path.join(remote_path, os.path.relpath(fname, local_path))

        if size == 0:
            continue

        if fname in remote_files:
            if get_usage() >= threshold:
                to_delete.append(fname)
            continue

        if TOTAL_UPLOAD - size > 0:
            while size != get_size(fname):
                time.sleep(30)
                size = get_size(fname)

            print("uploading", fname, remote_fname)
            rclone("copyto", fname, remote_fname)
            TOTAL_UPLOAD = TOTAL_UPLOAD - size

to_delete.sort(key=os.path.getctime)
for fname in to_delete:
    if get_usage() >= threshold:
        print("delete", fname)
        os.remove(fname)
