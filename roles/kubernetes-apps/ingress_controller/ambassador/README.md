# Installation Guide

- [Installation Guide](#installation-guide)
  - [Ambassador](#ambassador)
  - [Ambassador Operator](#ambassador-operator)
  - [Configuration](#configuration)
  - [Ingress annotations](#ingress-annotations)

## Ambassador

The Ambassador API Gateway provides all the functionality of a traditional ingress controller
(e.g., path-based routing) while exposing many additional capabilities such as authentication,
URL rewriting, CORS, rate limiting, and automatic metrics collection.

## Ambassador Operator

This addon deploys the Ambassador Operator, which in turn will install Ambassador in
a kubespray cluster.

The Ambassador Operator is a Kubernetes Operator that controls Ambassador's complete lifecycle
in your cluster, automating many of the repeatable tasks you would otherwise have to perform
yourself.  Once installed, the Operator will complete installations and seamlessly upgrade to new
versions of Ambassador as they become available.

## Configuration

- `ingress_ambassador_namespace` (default `ambassador`): namespace for installing Ambassador.
- `ingress_ambassador_update_window` (default `0 0 * * SUN`): _crontab_-like expression
  for specifying when the Operator should try to update the Ambassador API Gateway.
- `ingress_ambassador_version` (defaulkt: `*`): SemVer rule for versions allowed for
  installation/updates.

## Ingress annotations

The Ambassador API Gateway will automatically load balance `Ingress` resources
that include the annotation `kubernetes.io/ingress.class=ambassador`. All the other
resources will be just ignored.
