# Kernel Requirements

For Kubernetes >=1.32.0, the recommended kernel LTS version from the 4.x series is 4.19. Any 5.x or 6.x versions are also supported. For cgroups v2 support, the minimum version is 4.15 and the recommended version is 5.8+. Refer to [this link](https://github.com/kubernetes/kubernetes/blob/v1.32.0/vendor/k8s.io/system-validators/validators/types_unix.go#L33). For more information, see [kernel version requirements](https://kubernetes.io/docs/reference/node/kernel-version-requirements).

If the OS kernel version is lower than required, add the following configuration to ignore the kubeadm preflight errors:

```yaml
kubeadm_ignore_preflight_errors:
  - SystemVerification
```

The Kernel Version Matrixs:

| OS Verion          | Kernel Verion  | Kernel >=4.19      |
|---                 | ---            | ---                |
| RHEL 9             | 5.14           | :white_check_mark: |
| RHEL 8             | 4.18           | :x:                |
| Alma Linux 9       | 5.14           | :white_check_mark: |
| Alma Linux 8       | 4.18           | :x:                |
| Rocky Linux 9      | 5.14           | :white_check_mark: |
| Rocky Linux 8      | 4.18           | :x:                |
| Oracle Linux 9     | 5.14           | :white_check_mark: |
| Oracle Linux 8     | 4.18           | :x:                |
| Ubuntu 24.04       | 6.6            | :white_check_mark: |
| Ubuntu 22.04       | 5.15           | :white_check_mark: |
| Ubuntu 20.04       | 5.4            | :white_check_mark: |
| Debian 12          | 6.1            | :white_check_mark: |
| Debian 11          | 5.10           | :white_check_mark: |
| Fedora 40          | 6.8            | :white_check_mark: |
| Fedora 39          | 6.5            | :white_check_mark: |
| openSUSE Leap 15.5 | 5.14           | :white_check_mark: |
| Amazon Linux 2     | 4.14           | :x:                |
| openEuler 24.03    | 6.6            | :white_check_mark: |
| openEuler 22.03    | 5.10           | :white_check_mark: |
| openEuler 20.03    | 4.19           | :white_check_mark: |
