#!/usr/bin/env python3

import os
import subprocess

RCLONE_CONFIG_PATH = os.environ["RCLONE_CONFIG_PATH"]
RCLONE_REMOTE = os.getenv("RCLONE_REMOTE", "google_crypt:")
BACKUP_PATH = os.environ["BACKUP_PATH"]
EXCLUDE_FILE = os.environ["EXCLUDE_FILE"]
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD", "250"))
IGNORE = []

subprocess.run(["cp",RCLONE_CONFIG_PATH,"/tmp/rclone.conf"])

# read ignore files
with open(EXCLUDE_FILE) as f:
    for line in f.readlines():
        IGNORE.append(line.strip())


def rclone(*args):
    print(*args)
    return (
        subprocess.run(
            ["rclone", "--config", "/tmp/rclone.conf", *args], stdout=subprocess.PIPE
        )
        .stdout.decode("utf-8")
        .split("\n")
    )


def remoteF(fname):
    return os.path.relpath(fname, BACKUP_PATH)


def getFiles():
    files = []

    for line in rclone("ls", f"{RCLONE_REMOTE}/"):
        if " " not in line.strip():
            continue
        [size, basef] = line.strip().split(" ", 1)
        files.append({"size": int(size), "basef": basef})
    return files


def upload(fname, remote):
    return rclone("copyto", fname, f"{RCLONE_REMOTE}/{remote}")


# MAIN
TOTAL_UPLOAD = 0
uploaded_files = getFiles()
for root, subdir, files in os.walk(BACKUP_PATH):
    for f in files:
        fname = os.path.join(root, f)
        remote = remoteF(fname)

        # ignore symlinks
        if os.path.islink(fname):
            continue

        # make sure file is not to be ignored
        skip = False
        for ig in IGNORE:
            if ig in fname:
                skip = True
                break
        if skip:
            continue

        # make sure size doesnt exceed 700GB
        size_gb = MAX_UPLOAD
        try:
            size_gb = os.path.getsize(fname) / (1024 * 1024.0 * 1024.0)
        except:
            continue
        if TOTAL_UPLOAD + size_gb > MAX_UPLOAD:
            continue

        # check if we need to correct for size
        found = False
        for fobj in uploaded_files:
            if fobj["basef"] == remote:
                if fobj["size"] == os.path.getsize(fname):
                    found = True
                    break
        if found:
            continue

        # upload
        upload(fname, remote)
        TOTAL_UPLOAD = TOTAL_UPLOAD + size_gb
