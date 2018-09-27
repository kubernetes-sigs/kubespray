DigitalOcean
============

## Support

 * LoadBalancer creation via [digitalocean-cloud-controller-manager](https://github.com/digitalocean/digitalocean-cloud-controller-manager)
 * PersistentVolumes attached to Block Storage via [csi-digitalocean](https://github.com/digitalocean/csi-digitalocean)

## Example Configuration

```yaml
### Digital Ocean specific config
cloud_provider: digitalocean
## Provide your own API token
digitalocean_api_token: 
## Pick your ccm release: https://github.com/digitalocean/digitalocean-cloud-controller-manager/releases
digitalocean_ccm_version: v0.1.14
## Pick your csi release: https://github.com/digitalocean/csi-digitalocean/releases
digitalocean_csi_version: v1.1.0
kube_network_plugin: flannel
kubelet_preferred_address_types: InternalIP,ExternalIP,Hostname
docker_dns_servers_strict: false
## These are Digital Ocean specific DNS servers
upstream_dns_servers:
  - 67.207.67.3
  - 67.207.67.2
## Host names *must* be the same as the droplet name
override_system_hostname: false
```

## Notes

 * Droplets must be created with private networking enabled.
 * Use the droplet's private IP addresses when configuring kubespray.
 * Hostnames must match the droplet name, so you must set `override_system_hostname: false`.
 
## Cloud Init Example

For Ubuntu/Debian images, you can copy/paste this into the User Data
field on the droplet creation page. This will automatically install
initial dependencies for ansible:

```yaml
#cloud-config

## Ubuntu 18.04 ansible target

runcmd:
  - apt-get update && apt-get install -y python-minimal
```

