Large deployments of K8s
========================

For a large scaled deployments, consider the following configuration changes:

* Tune [ansible settings](http://docs.ansible.com/ansible/intro_configuration.html)
  for `forks` and `timeout` vars to fit large numbers of nodes being deployed.

* Override containers' `foo_image_repo` vars to point to intranet registry.

* Override the ``download_run_once: true`` and/or ``download_localhost: true``.
  See download modes for details.

* Adjust the `retry_stagger` global var as appropriate. It should provide sane
  load on a delegate (the first K8s master node) then retrying failed
  push or download operations.

* Tune parameters for DNS related applications (dnsmasq daemon set, kubedns
  replication controller). Those are ``dns_replicas``, ``dns_cpu_limit``,
  ``dns_cpu_requests``, ``dns_memory_limit``, ``dns_memory_requests``.
  Please note that limits must always be greater than or equal to requests.

For example, when deploying 200 nodes, you may want to run ansible with
``--forks=50``, ``--timeout=600`` and define the ``retry_stagger: 60``.
