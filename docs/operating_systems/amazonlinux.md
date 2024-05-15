# Amazon Linux 2

Amazon Linux is supported with docker,containerd and cri-o runtimes.

**Note:** that Amazon Linux is not currently covered in kubespray CI and
support for it is currently considered experimental.

Amazon Linux 2, while derived from the Redhat OS family, does not keep in
sync with RHEL upstream like CentOS/AlmaLinux/Oracle Linux. In order to use
Amazon Linux as the ansible host for your kubespray deployments you need to
manually install `python3` and deploy ansible and kubespray dependencies in
a python virtual environment or use the official kubespray containers.

There are no special considerations for using Amazon Linux as the target OS
for Kubespray deployments.
