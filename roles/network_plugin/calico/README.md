The yaml files in files/crds/kdd/ are used when Kubernetes is used as calico datastore (which is the default).

These files should be identical copies of:
https://github.com/projectcalico/calico/tree/master/_includes/charts/calico/crds/kdd

When updating the calico version, the CRDs should ideally be checked for differences and updated if needed. This is done by:
* clone the calico repository
* checkout using the same git tag as in Kubespray variable calico_version
* run recursive diff
* resolve any changes with files in Kubespray

The calico yaml files (as of v3.16.5) does not pass linting and are therefore excluded by a directive in the .yamllint file at the root of the repo.

Note: intentionally the yaml files are not changed in Kubespray but kept as is upstream!
