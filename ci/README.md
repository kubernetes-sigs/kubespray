# Kubespray CI on OKE

This directory contains the proposed OCI Resource Manager stack for the CI
cluster described in [issue #13507](https://github.com/kubernetes-sigs/kubespray/issues/13507).
It creates a dual-stack OKE cluster, one always-on bare metal worker, a second
bare metal node pool with zero to four workers, and a private Object Storage
bucket for CI artifacts. Applying this stack does not move the running CI
cluster or its workloads.

## Deploy with Resource Manager

1. In OCI Resource Manager, create a stack from this repository's Git source,
   selecting `master` and setting the working directory to `ci`. Run a plan
   first. See [Creating a Stack from Git](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/create-stack-git.htm).
2. Supply the required variables from [`terraform.tfvars.example`](terraform.tfvars.example)
   in the stack's Variables page. Select a currently supported OKE version and
   an OKE worker image for that version, region, and shape. Dual stack needs
   Kubernetes 1.29 or later and image build 754 or later. Confirm that the
   selected bare metal shape is supported by OKE and has capacity in the
   chosen availability domain.
3. Set `api_allowed_ipv4_cidrs` and, if needed, `api_allowed_ipv6_cidrs` to
   the maintainer networks that need direct Kubernetes API access. Empty lists
   deny public API ingress. Keep credentials and tenancy values in Resource
   Manager variables, not in Git.
4. Ensure the Resource Manager principal can create networking, OKE, and
   Object Storage resources. OKE also needs OCI's IPv6 IAM permissions in the
   target compartment. See [OKE IPv4 and IPv6 requirements](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/conteng_ipv4-and-ipv6.htm)
   and [cluster creation policies](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm).
5. Apply the reviewed plan. The second node pool starts at zero; set
   `on_demand_nodes` to a value from one through four and apply another plan
   to add capacity, then return it to zero when that capacity is no longer
   needed. This is manual scaling through Resource Manager.

The VCN uses `10.42.0.0/16` for IPv4 and an Oracle-assigned IPv6 `/56`.
The endpoint and worker/pod subnets are public dual-stack subnets as required
by OKE. Workers use a NAT gateway for IPv4 egress and an internet gateway for
IPv6 egress. Security lists allow traffic within the VCN; the API is exposed
to the configured CIDRs on TCP 6443. Review the network ranges against the
existing CI environment before applying.

## Remaining cutover work

The current Argo CD applications and their repository are not in Kubespray.
Before directing CI traffic at OKE, copy those manifests into this directory,
review their dependencies, install Argo CD in the new cluster, and bootstrap
the migrated applications from this repository. Remove MinIO from the desired
state, transfer any required objects to the new bucket, and update consumers
to use OCI Object Storage with credentials held outside Git. The bucket alone
does not migrate data or change application endpoints.

The CI guide describes both pod based and Vagrant/libvirt GitLab runners.
Validate both runner types on OKE bare metal, including host libvirt access,
storage, and dual-stack test jobs, before switching the GitLab runner
registration. Keep the existing cluster available for rollback until those
checks pass. This stack does not replace the current cluster automatically.
