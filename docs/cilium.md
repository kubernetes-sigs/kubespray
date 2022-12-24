# Cilium

## Kube-proxy replacement with Cilium

Cilium can run without kube-proxy by setting `cilium_kube_proxy_replacement`
to `strict`.

Without kube-proxy, cilium needs to know the address of the kube-apiserver
and this must be set globally for all cilium components (agents and operators).
Hence, in this configuration in Kubespray, Cilium will always contact
the external loadbalancer (even from a node in the control plane)
and if there is no external load balancer It will ignore any local load
balancer deployed by Kubespray and **only contacts the first master**.

## Cilium Operator

Unlike some operators, Cilium Operator does not exist for installation purposes.
> The Cilium Operator is responsible for managing duties in the cluster which should logically be handled once for the entire cluster, rather than once for each node in the cluster.

### Adding custom flags to the Cilium Operator

You can set additional cilium-operator container arguments using `cilium_operator_custom_args`.
This is an advanced option, and you should only use it if you know what you are doing.

Accepts an array or a string.

```yml
cilium_operator_custom_args: ["--foo=bar", "--baz=qux"]
```

or

```yml
cilium_operator_custom_args: "--foo=bar"
```

You do not need to add a custom flag to enable debugging. Instead, feel free to use the `CILIUM_DEBUG` variable.

### Adding extra volumes and mounting them

You can use `cilium_operator_extra_volumes` to add extra volumes to the Cilium Operator, and use `cilium_operator_extra_volume_mounts` to mount those volumes.
This is an advanced option, and you should only use it if you know what you are doing.

```yml
cilium_operator_extra_volumes:
  - configMap:
      name: foo
    name: foo-mount-path

cilium_operator_extra_volume_mounts:
  - mountPath: /tmp/foo/bar
    name: foo-mount-path
    readOnly: true
```

## Choose Cilium version

```yml
cilium_version: v1.12.1
```

## Add variable to config

Use following variables:

Example:

```yml
cilium_config_extra_vars:
  enable-endpoint-routes: true
```

## Change Identity Allocation Mode

Cilium assigns an identity for each endpoint. This identity is used to enforce basic connectivity between endpoints.

Cilium currently supports two different identity allocation modes:

- "crd" stores identities in kubernetes as CRDs (custom resource definition).
  - These can be queried with `kubectl get ciliumid`
- "kvstore" stores identities in an etcd kvstore.

## Enable Transparent Encryption

Cilium supports the transparent encryption of Cilium-managed host traffic and
traffic between Cilium-managed endpoints either using IPsec or Wireguard.

Wireguard option is only available in Cilium 1.10.0 and newer.

### IPsec Encryption

For further information, make sure to check the official [Cilium documentation.](https://docs.cilium.io/en/stable/gettingstarted/encryption-ipsec/)

To enable IPsec encryption, you just need to set three variables.

```yml
cilium_encryption_enabled: true
cilium_encryption_type: "ipsec"
```

The third variable is `cilium_ipsec_key.` You need to create a secret key string for this variable.
Kubespray does not automate this process.
Cilium documentation currently recommends creating a key using the following command:

```shell
echo "3 rfc4106(gcm(aes)) $(echo $(dd if=/dev/urandom count=20 bs=1 2> /dev/null | xxd -p -c 64)) 128"
```

Note that Kubespray handles secret creation. So you only need to pass the key as the `cilium_ipsec_key` variable.

### Wireguard Encryption

For further information, make sure to check the official [Cilium documentation.](https://docs.cilium.io/en/stable/gettingstarted/encryption-wireguard/)

To enable Wireguard encryption, you just need to set two variables.

```yml
cilium_encryption_enabled: true
cilium_encryption_type: "wireguard"
```

Kubespray currently supports Linux distributions with Wireguard Kernel mode on Linux 5.6 and newer.

## Bandwidth Manager

Cilium’s bandwidth manager supports the kubernetes.io/egress-bandwidth Pod annotation.

Bandwidth enforcement currently does not work in combination with L7 Cilium Network Policies.
In case they select the Pod at egress, then the bandwidth enforcement will be disabled for those Pods.

Bandwidth Manager requires a v5.1.x or more recent Linux kernel.

For further information, make sure to check the official [Cilium documentation.](https://docs.cilium.io/en/v1.12/gettingstarted/bandwidth-manager/)

To use this function, set the following parameters

```yml
cilium_enable_bandwidth_manager: true
```

## Install Cilium Hubble

k8s-net-cilium.yml:

```yml
cilium_enable_hubble: true ## enable support hubble in cilium
cilium_hubble_install: true ## install hubble-relay, hubble-ui
cilium_hubble_tls_generate: true ## install hubble-certgen and generate certificates
```

To validate that Hubble UI is properly configured, set up a port forwarding for hubble-ui service:

```shell script
kubectl port-forward -n kube-system svc/hubble-ui 12000:80
```

and then open [http://localhost:12000/](http://localhost:12000/).

## Hubble metrics

```yml
cilium_enable_hubble_metrics: true
cilium_hubble_metrics:
  - dns
  - drop
  - tcp
  - flow
  - icmp
  - http
```

[More](https://docs.cilium.io/en/v1.9/operations/metrics/#hubble-exported-metrics)

## Upgrade considerations

### Rolling-restart timeouts

Cilium relies on the kernel's BPF support, which is extremely fast at runtime but incurs a compilation penalty on initialization and update.

As a result, the Cilium DaemonSet pods can take a significant time to start, which scales with the number of nodes and endpoints in your cluster.

As part of cluster.yml, this DaemonSet is restarted, and Kubespray's [default timeouts for this operation](../roles/network_plugin/cilium/defaults/main.yml)
are not appropriate for large clusters.

This means that you will likely want to update these timeouts to a value more in-line with your cluster's number of nodes and their respective CPU performance.
This is configured by the following values:

```yaml
# Configure how long to wait for the Cilium DaemonSet to be ready again
cilium_rolling_restart_wait_retries_count: 30
cilium_rolling_restart_wait_retries_delay_seconds: 10
```

The total time allowed (count * delay) should be at least `($number_of_nodes_in_cluster * $cilium_pod_start_time)` for successful rolling updates. There are no
drawbacks to making it higher and giving yourself a time buffer to accommodate transient slowdowns.

Note: To find the `$cilium_pod_start_time` for your cluster, you can simply restart a Cilium pod on a node of your choice and look at how long it takes for it
to become ready.

Note 2: The default CPU requests/limits for Cilium pods is set to a very conservative 100m:500m which will likely yield very slow startup for Cilium pods. You
probably want to significantly increase the CPU limit specifically if short bursts of CPU from Cilium are acceptable to you.
