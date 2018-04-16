Contiv
======

Here is the [Contiv documentation](http://contiv.github.io/documents/).

## Administrate Contiv

There are two ways to manage Contiv:

* a web UI managed by the api proxy service
* a CLI named `netctl`


### Interfaces

#### The Web Interface

This UI is hosted on all kubernetes master nodes. The service is available at `https://<one of your master node>:10000`.

You can configure the api proxy by overriding the following variables:

```yaml
contiv_enable_api_proxy: true
contiv_api_proxy_port: 10000
contiv_generate_certificate: true
```

The default credentials to log in are: admin/admin.


#### The Command Line Interface

The second way to modify the Contiv configuration is to use the CLI. To do this, you have to connect to the server and export an environment variable to tell netctl how to connect to the cluster:

```bash
export NETMASTER=http://127.0.0.1:9999
```

The port can be changed by overriding the following variable:

```yaml
contiv_netmaster_port: 9999
```

The CLI doesn't use the authentication process needed by the web interface.


### Network configuration

The default configuration uses VXLAN to create an overlay. Two networks are created by default:

* `contivh1`: an infrastructure network. It allows nodes to access the pods IPs. It is mandatory in a Kubernetes environment that uses VXLAN.
* `default-net` : the default network that hosts pods.

You can change the default network configuration by overriding the `contiv_networks` variable.

The default forward mode is set to routing:

```yaml
contiv_fwd_mode: routing
```

The following is an example of how you can use VLAN instead of VXLAN:

```yaml
contiv_fwd_mode: bridge
contiv_vlan_interface: eth0
contiv_networks:
  - name: default-net
    subnet: "{{ kube_pods_subnet }}"
    gateway: "{{ kube_pods_subnet|ipaddr('net')|ipaddr(1)|ipaddr('address') }}"
    encap: vlan
    pkt_tag: 10
```
