# Cluster Hardening

If you want to improve the security on your cluster and make it compliant with the [CIS Benchmarks](https://learn.cisecurity.org/benchmarks), here you can find a configuration to harden your **kubernetes** installation.

To apply the hardening configuration, create a file (eg. `hardening.yaml`) and paste the content of the following code snippet into that.

## Minimum Requirements

The **kubernetes** version should be at least `v1.23.6` to have all the most recent security features (eg. the new `PodSecurity` admission plugin, etc).

**N.B.** Some of these configurations have just been added to **kubespray**, so ensure that you have the latest version to make it works properly. Also, ensure that other configurations doesn't override these.

`hardening.yaml`:

```yaml
# Hardening
---

## kube-apiserver
authorization_modes: ['Node', 'RBAC']
# AppArmor-based OS
# kube_apiserver_feature_gates: ['AppArmor=true']
kube_apiserver_request_timeout: 120s
kube_apiserver_service_account_lookup: true

# enable kubernetes audit
kubernetes_audit: true
audit_log_path: "/var/log/kube-apiserver-log.json"
audit_log_maxage: 30
audit_log_maxbackups: 10
audit_log_maxsize: 100

tls_min_version: VersionTLS12
tls_cipher_suites:
  - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
  - TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305

# enable encryption at rest
kube_encrypt_secret_data: true
kube_encryption_resources: [secrets]
kube_encryption_algorithm: "secretbox"

kube_apiserver_enable_admission_plugins:
  - EventRateLimit
  - AlwaysPullImages
  - ServiceAccount
  - NamespaceLifecycle
  - NodeRestriction
  - LimitRanger
  - ResourceQuota
  - MutatingAdmissionWebhook
  - ValidatingAdmissionWebhook
  - PodNodeSelector
  - PodSecurity
kube_apiserver_admission_control_config_file: true
# EventRateLimit plugin configuration
kube_apiserver_admission_event_rate_limits:
  limit_1:
    type: Namespace
    qps: 50
    burst: 100
    cache_size: 2000
  limit_2:
    type: User
    qps: 50
    burst: 100
kube_profiling: false

## kube-controller-manager
kube_controller_manager_bind_address: 127.0.0.1
kube_controller_terminated_pod_gc_threshold: 50
# AppArmor-based OS
# kube_controller_feature_gates: ["RotateKubeletServerCertificate=true", "AppArmor=true"]
kube_controller_feature_gates: ["RotateKubeletServerCertificate=true"]

## kube-scheduler
kube_scheduler_bind_address: 127.0.0.1
# AppArmor-based OS
# kube_scheduler_feature_gates: ["AppArmor=true"]

## etcd
etcd_deployment_type: kubeadm

## kubelet
kubelet_authorization_mode_webhook: true
kubelet_authentication_token_webhook: true
kube_read_only_port: 0
kubelet_rotate_server_certificates: true
kubelet_protect_kernel_defaults: true
kubelet_event_record_qps: 1
kubelet_rotate_certificates: true
kubelet_streaming_connection_idle_timeout: "5m"
kubelet_make_iptables_util_chains: true
kubelet_feature_gates: ["RotateKubeletServerCertificate=true", "SeccompDefault=true"]
kubelet_seccomp_default: true
kubelet_systemd_hardening: true
# In case you have multiple interfaces in your
# control plane nodes and you want to specify the right
# IP addresses, kubelet_secure_addresses allows you
# to specify the IP from which the kubelet
# will receive the packets.
kubelet_secure_addresses: "192.168.10.110 192.168.10.111 192.168.10.112"

# additional configurations
kube_owner: root
kube_cert_group: root

# create a default Pod Security Configuration and deny running of insecure pods
# kube_system namespace is exempted by default
kube_pod_security_use_default: true
kube_pod_security_default_enforce: restricted
```

Let's take a deep look to the resultant **kubernetes** configuration:

* The `anonymous-auth` (on `kube-apiserver`) is set to `true` by default. This is fine, because it is considered safe if you enable `RBAC` for the `authorization-mode`.
* The `enable-admission-plugins` has not the `PodSecurityPolicy` admission plugin. This because it is going to be definitely removed from **kubernetes** `v1.25`. For this reason we decided to set the newest `PodSecurity` (for more details, please take a look here: <https://kubernetes.io/docs/concepts/security/pod-security-admission/>). Then, we set the `EventRateLimit` plugin, providing additional configuration files (that are automatically created under the hood and mounted inside the `kube-apiserver` container) to make it work.
* The `encryption-provider-config` provide encryption at rest. This means that the `kube-apiserver` encrypt data that is going to be stored before they reach `etcd`. So the data is completely unreadable from `etcd` (in case an attacker is able to exploit this).
* The `rotateCertificates` in `KubeletConfiguration` is set to `true` along with `serverTLSBootstrap`. This could be used in alternative to `tlsCertFile` and `tlsPrivateKeyFile` parameters. Additionally it automatically generates certificates by itself, but you need to manually approve them or at least using an operator to do this (for more details, please take a look here: <https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet-tls-bootstrapping/>).
* If you are installing **kubernetes** in an AppArmor-based OS (eg. Debian/Ubuntu) you can enable the `AppArmor` feature gate uncommenting the lines with the comment `# AppArmor-based OS` on top.
* The `kubelet_systemd_hardening`, both with `kubelet_secure_addresses` setup a minimal firewall on the system. To better understand how these variables work, here's an explanatory image:
  ![kubelet hardening](img/kubelet-hardening.png)

Once you have the file properly filled, you can run the **Ansible** command to start the installation:

```bash
ansible-playbook -v cluster.yml \
        -i inventory.ini \
        -b --become-user=root \
        --private-key ~/.ssh/id_ecdsa \
        -e "@vars.yaml" \
        -e "@hardening.yaml"
```

**N.B.** The `vars.yaml` contains our general cluster information (SANs, load balancer, dns, etc..) and `hardening.yaml` is the file described above.

Once completed the cluster deployment, don't forget to approve the generated certificates (check them with `kubectl get csr`, approve with `kubectl certificate approve <csr_name>`). This action is necessary because the `secureTLSBootstrap` option and `RotateKubeletServerCertificate` feature gate for `kubelet` are enabled (CIS [4.2.11](https://www.tenable.com/audits/items/CIS_Kubernetes_v1.20_v1.0.0_Level_1_Worker.audit:05af3dfbca8e0c3fb3559c6c7de29191), [4.2.12](https://www.tenable.com/audits/items/CIS_Kubernetes_v1.20_v1.0.0_Level_1_Worker.audit:5351c76f8c5bff8f98c29a5200a35435)).
