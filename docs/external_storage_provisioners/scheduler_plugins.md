# Scheduler plugins for Kubernetes

[scheduler-plugins](https://github.com/kubernetes-sigs/scheduler-plugins) is out-of-tree scheduler plugins based on the [scheduler framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/).

The kube-scheduler binary includes a list of plugins:

- [CapacityScheduling](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/capacityscheduling) [Beta]
- [CoScheduling](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/coscheduling) [Beta]
- [NodeResources](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/noderesources) [Beta]
- [NodeResouceTopology](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/noderesourcetopology/README.md) [Beta]
- [PreemptionToleration](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/preemptiontoleration/README.md) [Alpha]
- [Trimaran](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/trimaran/README.md) [Alpha]
- [NetworkAware](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/networkaware/README.md) [Sample]
- [CrossNodePreemption](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/crossnodepreemption/README.md) [Sample]
- [PodState](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/podstate/README.md) [Sample]
- [QualityOfService](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/pkg/qos/README.md) [Sample]

Currently, we use [helm chart](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/manifests/install/charts/as-a-second-scheduler/README.md#installing-the-chart) to install the scheduler plugins, so that a second scheduler would be created and running. **Note that running multi-scheduler will inevitably encounter resource conflicts when the cluster is short of resources**.

## Compatibility Matrix

There are requirements for the version of Kubernetes, please see [Compatibility Matrix
](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master?tab=readme-ov-file#compatibility-matrix). It deserves our attention.

| Scheduler Plugins | Compiled With K8s Version |
| ----------------- | ------------------------- |
| v0.28.9           | v1.28.9                   |
| v0.27.8           | v1.27.8                   |

## Turning it on

  The `scheduler_plugins_enabled` option is used to enable the installation of scheduler plugins.

  You can enable or disable some plugins by setting the `scheduler_plugins_enabled_plugins` or `scheduler_plugins_disabled_plugins` option. They must be in the list we mentioned above.

  In addition, to use custom plugin configuration, set a value for `scheduler_plugins_plugin_config` option.

  For example, for Coscheduling plugin, you want to customize the permit waiting timeout to 10 seconds:

  ```yaml
  scheduler_plugins_plugin_config:
    - name: Coscheduling
      args:
        permitWaitingTimeSeconds: 10 # default is 60
  ```

## Leverage plugin

  Once the plugin is installed, we can apply CRs into cluster. For example, if using `CoScheduling`, we can apply the CR and test the deployment in the [example](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/doc/install.md#test-coscheduling).
