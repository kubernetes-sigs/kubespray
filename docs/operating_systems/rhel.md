# Red Hat Enterprise Linux (RHEL)

The documentation also applies to Red Hat derivatives, including Alma Linux, Rocky Linux, Oracle Linux, and CentOS.

## RHEL Support Subscription Registration

The content of this section does not apply to open-source derivatives.

In order to install packages via yum or dnf, RHEL hosts are required to be registered for a valid Red Hat support subscription.

You can apply for a 1-year Development support subscription by creating a [Red Hat Developers](https://developers.redhat.com/) account. Be aware though that as the Red Hat Developers subscription is limited to only 1 year, it should not be used to register RHEL hosts provisioned in Production environments.

Once you have a Red Hat support account, simply add the credentials to the Ansible inventory parameters `rh_subscription_username` and `rh_subscription_password` prior to deploying Kubespray. If your company has a Corporate Red Hat support account, then obtain an **Organization ID** and **Activation Key**, and add these to the Ansible inventory parameters `rh_subscription_org_id` and `rh_subscription_activation_key` instead of using your Red Hat support account credentials.

```ini
rh_subscription_username: ""
rh_subscription_password: ""
# rh_subscription_org_id: ""
# rh_subscription_activation_key: ""
```

Either the Red Hat support account username/password, or Organization ID/Activation Key combination must be specified in the Ansible inventory in order for the Red Hat subscription registration to complete successfully during the deployment of Kubespray.

Update the Ansible inventory parameters `rh_subscription_usage`, `rh_subscription_role` and `rh_subscription_sla` if necessary to suit your specific requirements.

```ini
rh_subscription_usage: "Development"
rh_subscription_role: "Red Hat Enterprise Server"
rh_subscription_sla: "Self-Support"
```

If the RHEL hosts are already registered to a valid Red Hat support subscription via an alternative configuration management approach prior to the deployment of Kubespray, the successful RHEL `subscription-manager` status check will simply result in the RHEL subscription registration tasks being skipped.

## RHEL 8 Family

RHEL 8, AlmaLinux 8, and Rocky Linux 8 are not end-of-life, but they are no longer in full or active support. RHEL 8 remains in maintenance support, while AlmaLinux 8 and Rocky Linux 8 receive security maintenance, through May 31, 2029. Prefer a newer major release for new deployments; this guidance is intended primarily for existing RHEL 8 family environments. See the lifecycle documentation for [RHEL](https://access.redhat.com/support/policy/updates/errata), [AlmaLinux](https://wiki.almalinux.org/release-notes/), and [Rocky Linux](https://wiki.rockylinux.org/rocky/version/).

With `bootstrap_os_install_python: true` (the default), the shared `centos.yml` bootstrap checks the selected interpreter before gathering facts, without restricting the distribution or OS version. If Python is missing or older than 3.9, it installs Python 3.12 using `yum`, preserving system Python for DNF. This requires repositories providing `python3.12`, available in AlmaLinux 8.10 and Rocky Linux 8.10. RHEL uses a separate bootstrap path and is unchanged.

If the inventory pins an older interpreter, set:

```yaml
ansible_python_interpreter: /usr/bin/python3.12
```

The default containerd binaries require a newer glibc than EL8 provides. Use the static binaries on these systems:

```yaml
containerd_static_binary: true
```

Run bootstrap before `--check` on fresh hosts. Experimental CI includes `rockylinux8-calico` in the regular PR matrix and `almalinux8-calico` as a manual job. Both use static containerd binaries. SELinux, runtime, and kernel/cgroup compatibility still need validation; the kernel check and cgroup v1 exceptions are not production recommendations.

## Rocky Linux 10

(Experimental in Kubespray CI)

The official Rocky Linux 10 cloud image does not include `kernel-modules-extra`. Both Kube Proxy and CNI rely on this package, and since it relates to kernel version compatibility (which may require VM reboots, etc.), we haven't found an ideal solution.

However, some users report that it doesn't affect them (minimal version). Therefore, the Kubespray CI Rocky Linux 10 image is built by Kubespray maintainers using `diskimage-builder`. For detailed methods, please refer to [the comments](https://github.com/kubernetes-sigs/kubespray/pull/12355#issuecomment-3705400093).
