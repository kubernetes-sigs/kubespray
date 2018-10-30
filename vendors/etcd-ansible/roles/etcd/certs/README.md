
### Roles

####  [roles/etcd/certs/ca](https://github.com/ant31/etcd-ansible/blob/master/roles/etcd/certs/ca)

Must be called or delegated to the `[etcd-cert-managers]` hosts.
It installs the `cfssl` binaries, and creates the peer-ca and client-ca certificates.
##### Variables
###### cfssl_version
Version of the cfssl binary

#### [roles/etcd/certs/generate](https://github.com/ant31/etcd-ansible/blob/master/roles/etcd/certs/generate)

Must be called or delegated to the `[etcd-cert-managers]` hosts.

The role is generating the certificate for the etcd-client and etcd-peers.
Each host gets a unique certificate, they are stored in `{{etcd_cert_dir}}/{host}}`.
A tarball for each is created and saved as a fact in the `etcd_cert_tarballs_b64` host-variables.

In most cases this role is not called directly, but via the `etcd/certs/fetch` role. 

##### Variables
###### etcd_hosts
Generate certificates for all the listed hosts in the `etcd_hosts` variable
If empty or non-defined, it generates certificates for all known hosts (`groups['etcd'] | union(groups['etcd-clients'])`).

The variable is automatically set to `[{{inventory_hostname}}]` when called via `etcd/certs/fetch`.
```
etcd_hosts: [{{inventory_hostname}}]
```

####  [roles/etcd/certs/fetch](https://github.com/ant31/etcd-ansible/blob/master/roles/etcd/certs/fetch)

Must be called from all `[etcd]` and `[etcd-clients]` nodes.
This role calls `etcd/certs/generate` as a dependency and in addition download to the current host its certificate. 
It all set the cert serial in the `etcd_client_cert_serial` and `etcd_peer_cert_serial` host-variables.

##### Variables
###### etcd_skip_certs
if true, the role doesn't try to retrieve the cert tarball from the `[etcd-cert-managers]`, it assumes that it was already done on a previous run. Running the role with this `etcd_skip_certs=true` will only configure `etcd_client_cert_serial` and `etcd_peer_cert_serial` vars.

if `etcd_action1 != 'create'`, this variable is automatically set to `true`. 
 
