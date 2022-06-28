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
cilium_version: v1.11.3
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
