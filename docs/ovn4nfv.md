# OVN4NFV-k8S-Plugin

Intro to [ovn4nfv-k8s-plugin](https://github.com/opnfv/ovn4nfv-k8s-plugin)

## How to use it

* Enable ovn4nfv in `group_vars/k8s-cluster/k8s-cluster.yml`

```yml
...
kube_network_plugin: ovn4nfv
...
```

## Verifying ovn4nfv kube network plugin

* ovn4nfv install ovn control plan in the master and ovn daemonset in all nodes
* Network function Networking(nfn) operator is install in the master and nfn agent is installed in all the node
* ovn4nfv install `ovn4nfvk8s-cni` cni shim binary in `/opt/cni/bin/` and nfn agent act as the cni server
* All ovn4nfv pods are installed in the kube-system

```ShellSession
# From K8s client
# kubectl get pods -n kube-system -l app=ovn-control-plane -o wide
NAME                                 READY   STATUS    RESTARTS   AGE     IP               NODE     NOMINATED NODE   READINESS GATES
ovn-control-plane-5f8b7bcc65-w759g   1/1     Running   0          3d18h   192.168.121.25   master   <none>           <none>

# kubectl get pods -n kube-system -l app=ovn-controller -o wide
NAME                   READY   STATUS    RESTARTS   AGE     IP               NODE       NOMINATED NODE   READINESS GATES
ovn-controller-54zzj   1/1     Running   0          3d18h   192.168.121.24   minion01   <none>           <none>
ovn-controller-7cljt   1/1     Running   0          3d18h   192.168.121.25   master     <none>           <none>
ovn-controller-cx46g   1/1     Running   0          3d18h   192.168.121.15   minion02   <none>           <none>

# kubectl get pods -n kube-system -l name=nfn-operator -o wide
NAME                            READY   STATUS    RESTARTS   AGE     IP               NODE     NOMINATED NODE   READINESS GATES
nfn-operator-6dc44dbf48-xk9zl   1/1     Running   0          3d18h   192.168.121.25   master   <none>           <none>

# kubectl get pods -n kube-system -l app=nfn-agent -o wide
NAME              READY   STATUS    RESTARTS   AGE     IP               NODE       NOMINATED NODE   READINESS GATES
nfn-agent-dzlpp   1/1     Running   0          3d18h   192.168.121.15   minion02   <none>           <none>
nfn-agent-jcdbn   1/1     Running   0          3d18h   192.168.121.25   master     <none>           <none>
nfn-agent-lrkzk   1/1     Running   0          3d18h   192.168.121.24   minion01   <none>           <none>

# kubectl get pods -n kube-system -l app=ovn4nfv -o wide
NAME                READY   STATUS    RESTARTS   AGE     IP               NODE       NOMINATED NODE   READINESS GATES
ovn4nfv-cni-5zdz2   1/1     Running   0          3d18h   192.168.121.24   minion01   <none>           <none>
ovn4nfv-cni-k5wjp   1/1     Running   0          3d18h   192.168.121.25   master     <none>           <none>
ovn4nfv-cni-t6z5b   1/1     Running   0          3d18h   192.168.121.15   minion02   <none>           <none>
```
