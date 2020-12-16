
# Ambassador

The [Ambassador API Gateway](https://github.com/datawire/ambassador) provides all the functionality of a traditional ingress controller
(e.g., path-based routing) while exposing many additional capabilities such as authentication,
URL rewriting, CORS, rate limiting, and automatic metrics collection.

## Installation

### Configuration

* `ingress_ambassador_namespace` (default `ambassador`): namespace for installing Ambassador.
* `ingress_ambassador_update_window` (default `0 0 * * SUN`): _crontab_-like expression
  for specifying when the Operator should try to update the Ambassador API Gateway.
* `ingress_ambassador_version` (default: `*`): SemVer rule for versions allowed for
  installation/updates.
* `ingress_ambassador_secure_port` (default: 443): HTTPS port to listen at.
* `ingress_ambassador_insecure_port` (default: 80): HTTP port to listen at.

### Ambassador Operator

This Ambassador addon deploys the Ambassador Operator, which in turn will install
the [Ambassador API Gateway](https://github.com/datawire/ambassador) in
a Kubernetes cluster.

The Ambassador Operator is a Kubernetes Operator that controls Ambassador's complete lifecycle
in your cluster, automating many of the repeatable tasks you would otherwise have to perform
yourself.  Once installed, the Operator will complete installations and seamlessly upgrade to new
versions of Ambassador as they become available.

## Usage

The following example creates simple http-echo services and an `Ingress` object
to route to these services.

Note well that the [Ambassador API Gateway](https://github.com/datawire/ambassador) will automatically load balance `Ingress` resources
that include the annotation `kubernetes.io/ingress.class=ambassador`. All the other
resources will be just ignored.

```yaml
kind: Pod
apiVersion: v1
metadata:
  name: foo-app
  labels:
    app: foo
spec:
  containers:
  - name: foo-app
    image: hashicorp/http-echo
    args:
    - "-text=foo"
---
kind: Service
apiVersion: v1
metadata:
  name: foo-service
spec:
  selector:
    app: foo
  ports:
  # Default port used by the image
  - port: 5678
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    kubernetes.io/ingress.class: ambassador
spec:
  rules:
  - http:
      paths:
      - path: /foo
        backend:
          serviceName: foo-service
          servicePort: 5678
```

Now you can test that the ingress is working with curl:

```console
$ export AMB_IP=$(kubectl get service ambassador -n ambassador -o 'go-template={{range .status.loadBalancer.ingress}}{{print .ip "\n"}}{{end}}')
$ curl $AMB_IP/foo
foo
```
