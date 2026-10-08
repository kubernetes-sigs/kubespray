#!/usr/bin/env python3
"""Renew the certificates managed by kubeadm if they expire before the next
scheduled run of the k8s-certs-renew timer."""

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

DAYS_BUFFER = 7  # time margin, because we should not renew at the last moment


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kubeadm", required=True,
                        help="path to the kubeadm binary")
    parser.add_argument("--calendar", required=True,
                        help="systemd calendar spec of the renewal timer")
    parser.add_argument("--admin-conf", required=True,
                        help="path to the kubeadm admin.conf")
    parser.add_argument("--apiserver-port", type=int, required=True,
                        help="local apiserver port to wait on after the restart")
    runtime = parser.add_mutually_exclusive_group(required=True)
    runtime.add_argument("--crictl",
                         help="path to crictl, used to restart the control plane pods")
    runtime.add_argument("--docker",
                         help="path to docker, used to restart the control plane pods")
    return parser.parse_args()


def log(message):
    print(message, flush=True)


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def next_scheduled_run(calendar):
    """Next elapse of the renewal timer, or None if it cannot be determined."""
    # systemctl show reports an empty NextElapseUSecRealtime while the timer's
    # unit is running, so use the calendar spec to get the next scheduled run.
    # TZ=UTC makes the output format the same in all timezones. The offset
    # that this causes is small compared to DAYS_BUFFER.
    env = dict(os.environ, LC_ALL="C", TZ="UTC")
    try:
        output = run(
            ["systemd-analyze", "calendar", calendar],
            stdout=subprocess.PIPE,
            env=env,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    for line in output.splitlines():
        label, _, value = line.partition(":")
        if label.strip() == "Next elapse":
            try:
                # "Mon 2026-10-05 03:00:00 UTC" or "never"
                elapse = datetime.strptime(value.strip(), "%a %Y-%m-%d %H:%M:%S UTC")
            except ValueError:
                return None
            return elapse.replace(tzinfo=timezone.utc)
    return None


def certs_to_renew(kubeadm, threshold):
    output = run(
        [kubeadm, "certs", "check-expiration", "-o", "json"],
        stdout=subprocess.PIPE,
    ).stdout
    expiring = []
    for cert in json.loads(output)["certificates"]:
        # Ignore missing certs, kubeadm cannot renew them. For example,
        # super-admin.conf is only on the node where "kubeadm init" ran.
        if cert["missing"]:
            continue
        expiration = datetime.strptime(cert["expirationDate"], "%Y-%m-%dT%H:%M:%S%z")
        if expiration < threshold:
            expiring.append(cert["name"])
    return expiring


def restart_control_plane(args):
    if args.docker:
        list_cmd = [args.docker, "ps", "-a", "-q",
                    "-f", "name=k8s_POD_(kube-apiserver|kube-controller-manager|kube-scheduler|etcd)-*"]
        remove_cmd = [args.docker, "rm", "-f"]
    else:
        list_cmd = [args.crictl, "pods", "--namespace", "kube-system", "-q",
                    "--name", "kube-scheduler-*|kube-controller-manager-*|kube-apiserver-*|etcd-*"]
        remove_cmd = [args.crictl, "rmp", "-f"]
    pods = run(list_cmd, stdout=subprocess.PIPE).stdout.split()
    if pods:
        run(remove_cmd + pods)


def wait_for_apiserver(port):
    while True:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(1)


def main():
    args = parse_args()

    log("## Check expiration before renewal ##")
    run([args.kubeadm, "certs", "check-expiration"])

    next_run = next_scheduled_run(args.calendar)
    if next_run is None:
        log("## Cannot get the next scheduled run from the systemd calendar, renew directly ##")
    else:
        expiring = certs_to_renew(args.kubeadm, next_run + timedelta(days=DAYS_BUFFER))
        if not expiring:
            log("## Skip cert renew and K8S container restart, since all certificates expire after the next scheduled run ##")
            return
        log("## Certificates to renew: ##")
        log("\n".join(expiring))

    log("## Renewing certificates managed by kubeadm ##")
    run([args.kubeadm, "certs", "renew", "all"])

    log("## Restarting control plane pods managed by kubeadm ##")
    restart_control_plane(args)

    log("## Updating /root/.kube/config ##")
    shutil.copy(args.admin_conf, "/root/.kube/config")

    log("## Waiting for apiserver to be up again ##")
    wait_for_apiserver(args.apiserver_port)

    log("## Expiration after renewal ##")
    run([args.kubeadm, "certs", "check-expiration"])


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as err:
        log(f"Command {err.cmd} failed with return code {err.returncode}")
        sys.exit(err.returncode)
