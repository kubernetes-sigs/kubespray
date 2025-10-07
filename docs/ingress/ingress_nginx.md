# Installation Guide

## Contents

- [Prerequisite Generic Deployment Command](#prerequisite-generic-deployment-command)
  - [Provider Specific Steps](#provider-specific-steps)
    - [Docker for Mac](#docker-for-mac)
    - [minikube](#minikube)
    - [AWS](#aws)
    - [GCE - GKE](#gce-gke)
    - [Azure](#azure)
    - [Bare-metal](#bare-metal)
  - [Verify installation](#verify-installation)
  - [Detect installed version](#detect-installed-version)
- [Using Helm](#using-helm)

## Prerequisite Generic Deployment Command

!!! attention
    The default configuration watches Ingress object from *all the namespaces*.
    To change this behavior use the flag `--watch-namespace` to limit the scope to a particular namespace.

!!! warning
    If multiple Ingresses define different paths for the same host, the ingress controller will merge the definitions.

!!! attention
    If you're using GKE you need to initialize your user as a cluster-admin with the following command:

```console
kubectl create clusterrolebinding cluster-admin-binding \
--clusterrole cluster-admin \
--user $(gcloud config get-value account)
```

The following **Mandatory Command** is required for all deployments except for AWS. See below for the AWS version.

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.3/deploy/static/provider/cloud/deploy.yaml
```

### Provider Specific Steps

There are cloud provider specific yaml files.

#### Docker for Mac

Kubernetes is available in Docker for Mac (from [version 18.06.0-ce](https://docs.docker.com/docker-for-mac/release-notes/#stable-releases-of-2018))

First you need to [enable kubernetes](https://docs.docker.com/docker-for-mac/#kubernetes).

Then you have to create a service:

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud-generic.yaml
```

#### minikube

For standard usage:

```console
minikube addons enable ingress
```

For development:

1. Disable the ingress addon:

```console
minikube addons disable ingress
```

1. Execute `make dev-env`
1. Confirm the `nginx-ingress-controller` deployment exists:

```console
$ kubectl get pods -n ingress-nginx
NAME                                       READY     STATUS    RESTARTS   AGE
default-http-backend-66b447d9cf-rrlf9      1/1       Running   0          12s
nginx-ingress-controller-fdcdcd6dd-vvpgs   1/1       Running   0          11s
```

#### AWS

In AWS we use an Elastic Load Balancer (ELB) to expose the NGINX Ingress controller behind a Service of `Type=LoadBalancer`.
Since Kubernetes v1.9.0 it is possible to use a classic load balancer (ELB) or network load balancer (NLB)
Please check the [elastic load balancing AWS details page](https://aws.amazon.com/elasticloadbalancing/details/)

##### Elastic Load Balancer - ELB

This setup requires to choose in which layer (L4 or L7) we want to configure the Load Balancer:

- [Layer 4](https://en.wikipedia.org/wiki/OSI_model#Layer_4:_Transport_Layer): Use an Network Load Balancer (NLB) with TCP as the listener protocol for ports 80 and 443.
- [Layer 7](https://en.wikipedia.org/wiki/OSI_model#Layer_7:_Application_Layer): Use an Elastic Load Balancer (ELB) with HTTP as the listener protocol for port 80 and terminate TLS in the ELB

For L4:

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/aws/deploy.yaml
```

For L7:

Change the value of `service.beta.kubernetes.io/aws-load-balancer-ssl-cert` in the file `provider/aws/deploy-tls-termination.yaml` replacing the dummy id with a valid one. The dummy value is `"arn:aws:acm:us-west-2:XXXXXXXX:certificate/XXXXXX-XXXXXXX-XXXXXXX-XXXXXXXX"`

Check that no change is necessary with regards to the ELB idle timeout. In some scenarios, users may want to modify the ELB idle timeout, so please check the [ELB Idle Timeouts section](#elb-idle-timeouts) for additional information. If a change is required, users will need to update the value of `service.beta.kubernetes.io/aws-load-balancer-connection-idle-timeout` in `provider/aws/deploy-tls-termination.yaml`

Then execute:

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/aws/deploy-tls-termination.yaml
```

This example creates an ELB with just two listeners, one in port 80 and another in port 443

![Listeners](https://github.com/kubernetes/ingress-nginx/blob/main/docs/images/elb-l7-listener.png)

##### ELB Idle Timeouts

In some scenarios users will need to modify the value of the ELB idle timeout.
Users need to ensure the idle timeout is less than the [keepalive_timeout](http://nginx.org/en/docs/http/ngx_http_core_module.html#keepalive_timeout) that is configured for NGINX.
By default NGINX `keepalive_timeout` is set to `75s`.

The default ELB idle timeout will work for most scenarios, unless the NGINX [keepalive_timeout](http://nginx.org/en/docs/http/ngx_http_core_module.html#keepalive_timeout) has been modified,
in which case `service.beta.kubernetes.io/aws-load-balancer-connection-idle-timeout` will need to be modified to ensure it is less than the `keepalive_timeout` the user has configured.

*Please Note: An idle timeout of `3600s` is recommended when using WebSockets.*

More information with regards to idle timeouts for your Load Balancer can be found in the [official AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/classic/config-idle-timeout.html).

##### Network Load Balancer (NLB)

This type of load balancer is supported since v1.10.0 as an ALPHA feature.

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/aws/service-nlb.yaml
```

#### GCE-GKE

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud-generic.yaml
```

**Important Note:** proxy protocol is not supported in GCE/GKE

#### Azure

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/master/deploy/static/provider/cloud-generic.yaml
```

#### Bare-metal

Using [NodePort](https://kubernetes.io/docs/concepts/services-networking/service/#type-nodeport):

```console
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml
```

!!! tip
    For extended notes regarding deployments on bare-metal, see [Bare-metal considerations](https://github.com/kubernetes/ingress-nginx/blob/main/docs/deploy/baremetal.md).

### Verify installation

To check if the ingress controller pods have started, run the following command:

```console
kubectl get pods --all-namespaces -l app.kubernetes.io/name=ingress-nginx --watch
```

Once the operator pods are running, you can cancel the above command by typing `Ctrl+C`.
Now, you are ready to create your first ingress.

### Detect installed version

To detect which version of the ingress controller is running, exec into the pod and run `nginx-ingress-controller version` command.

```console
POD_NAMESPACE=ingress-nginx
POD_NAME=$(kubectl get pods -n $POD_NAMESPACE -l app.kubernetes.io/component=controller -o jsonpath='{.items[0].metadata.name}')

kubectl exec -it $POD_NAME -n $POD_NAMESPACE -- /nginx-ingress-controller --version
```

## Using Helm

NGINX Ingress controller can be installed via [Helm](https://helm.sh/) using the chart [ingress-nginx/ingress-nginx](https://kubernetes.github.io/ingress-nginx).
Official documentation is [here](https://kubernetes.github.io/ingress-nginx/deploy/#using-helm)

To install the chart with the release name `my-nginx`:

```console
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install my-nginx ingress-nginx/ingress-nginx
```

Detect installed version:

```console
POD_NAME=$(kubectl get pods -l app.kubernetes.io/name=ingress-nginx -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD_NAME -- /nginx-ingress-controller --version
```
