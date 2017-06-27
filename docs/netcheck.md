Network Checker Application
===========================

With the ``deploy_netchecker`` var enabled (defaults to false), Kubespray deploys a
Network Checker Application from the 3rd side `l23network/k8s-netchecker` docker
images. It consists of the server and agents trying to reach the server by usual
for Kubernetes applications network connectivity meanings. Therefore, this
automagically verifies a pod to pod connectivity via the cluster IP and checks
if DNS resolve is functioning as well.

The checks are run by agents on a periodic basis and cover standard and host network
pods as well. The history of performed checks may be found in the agents' application
logs.

To get the most recent and cluster-wide network connectivity report, run from
any of the cluster nodes:
```
curl http://localhost:31081/api/v1/connectivity_check
```
Note that Kubespray does not invoke the check but only deploys the application, if
requested.

There are related application specifc variables:
```
netchecker_port: 31081
agent_report_interval: 15
netcheck_namespace: default
agent_img: "quay.io/l23network/k8s-netchecker-agent:v1.0"
server_img: "quay.io/l23network/k8s-netchecker-server:v1.0"
```

Note that the application verifies DNS resolve for FQDNs comprising only the
combination of the ``netcheck_namespace.dns_domain`` vars, for example the
``netchecker-service.default.cluster.local``. If you want to deploy the application
to the non default namespace, make sure as well to adjust the ``searchdomains`` var
so the resulting search domain records to contain that namespace, like:

```
search: foospace.cluster.local default.cluster.local ...
nameserver: ...
```
