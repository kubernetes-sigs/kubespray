Hashicorp Vault Role
====================

Overview
--------

The Vault role is a two-step process:

1. Bootstrap

You cannot start your certificate management service securely with SSL (and 
the datastore behind it) without having the certificates in-hand already. This
presents an unfortunate chicken and egg scenario, with one requiring the other.
To solve for this, the Bootstrap step was added.

This step spins up a temporary instance of Vault to issue certificates for
Vault itself. It then leaves the temporary instance running, so that the Etcd
role can generate certs for itself as well. Eventually, this may be improved
to allow alternate backends (such as Consul), but currently the tasks are
hardcoded to only create a Vault role for Etcd.

2. Cluster

This step is where the long-term Vault cluster is started and configured. Its
first task, is to stop any temporary instances of Vault, to free the port for
the long-term. At the end of this task, the entire Vault cluster should be up
and ready to go.

Keys to the Kingdom
-------------------

The two most important security pieces of Vault are the ``root_token``
and ``unsealing_keys``. Both of these values are given exactly once, during
the initialization of the Vault cluster. For convenience, they are saved
to the ``vault_secret_dir`` (default: /etc/vault/secrets) of every host in the
vault group.

It is *highly* recommended that these secrets are removed from the servers after
your cluster has been deployed, and kept in a safe location of your choosing.
Naturally, the seriousness of the situation depends on what you're doing with
your Kubespray cluster, but with these secrets, an attacker will have the ability
to authenticate to almost everything in Kubernetes and decode all private
(HTTPS) traffic on your network signed by Vault certificates.

For even greater security, you may want to remove and store elsewhere any
CA keys generated as well (e.g. /etc/vault/ssl/ca-key.pem).

Vault by default encrypts all traffic to and from the datastore backend, all
resting data, and uses TLS for its TCP listener. It is recommended that you
do not change the Vault config to disable TLS, unless you absolutely have to.

Usage
-----

To get the Vault role running, you must to do two things at a minimum:

1. Assign the ``vault`` group to at least 1 node in your inventory
1. Change ``cert_management`` to be ``vault`` instead of ``script``

Nothing else is required, but customization is possible. Check
``roles/vault/defaults/main.yml`` for the different variables that can be
overridden, most common being ``vault_config``, ``vault_port``, and
``vault_deployment_type``.

As a result of the Vault role will be create separated Root CA for `etcd`,
`kubernetes` and `vault`. Also, if you intend to use a Root or Intermediate CA
generated elsewhere, you'll need to copy the certificate and key to the hosts in the vault group prior to running the vault role. By default, they'll be located at:

* vault:
  * ``/etc/vault/ssl/ca.pem``
  * ``/etc/vault/ssl/ca-key.pem``
* etcd:
  * ``/etc/ssl/etcd/ssl/ca.pem``
  * ``/etc/ssl/etcd/ssl/ca-key.pem``
* kubernetes:
  * ``/etc/kubernetes/ssl/ca.pem``
  * ``/etc/kubernetes/ssl/ca-key.pem``

Additional Notes:

- ``groups.vault|first`` is considered the source of truth for Vault variables
- ``vault_leader_url`` is used as pointer for the current running Vault
- Each service should have its own role and credentials. Currently those 
  credentials are saved to ``/etc/vault/roles/<role>/``. The service will
  need to read in those credentials, if they want to interact with Vault.

Potential Work
--------------

- Change the Vault role to not run certain tasks when ``root_token`` and
  ``unseal_keys`` are not present. Alternatively, allow user input for these
  values when missing.
- Add the ability to start temp Vault with Host, Rkt, or Docker
- Add a dynamic way to change out the backend role creation during Bootstrap,
  so other services can be used (such as Consul)
