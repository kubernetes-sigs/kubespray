Large deployments of K8s
========================

For a large scaled deployments, consider the following configuration changes:

* Tune [ansible settings](http://docs.ansible.com/ansible/intro_configuration.html)
  for `forks` and `timeout` vars to fit large numbers of nodes being deployed.

* Override containers' `foo_image_repo` vars to point to intranet registry.

* Override the ``download_run_once: true`` to download binaries and container
  images only once then push to nodes in batches.

* Adjust the `retry_stagger` global var as appropriate. It should provide sane
  load on a delegate (the first K8s master node) then retrying failed
  push or download operations.

For example, when deploying 200 nodes, you may want to run ansible with
``--forks=50``, ``--timeout=600`` and define the ``retry_stagger: 60``.
