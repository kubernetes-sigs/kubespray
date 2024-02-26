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

Currently supports selection of deployment modes by switching the `scheduler_plugins_single_scheduler_mode` (bool) option:

- **single-scheduler mode** (default):

    Only one scheduler is running. That would patch and replace the default scheduler. It's recommended for the production env.

- **second-scheduler mode**:

    Two schedulers are running. One is the default scheduler, and the other is the scheduler-plugins's scheduler.

**Note that running multi-scheduler will inevitably encounter resource conflicts when the cluster is short of resources**.

## Compatibility Matrix

There are requirements for the version of Kubernetes, please see [Compatibility Matrix
](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master?tab=readme-ov-file#compatibility-matrix). It deserves our attention.

| Scheduler Plugins | Compiled With K8s Version |
| ----------------- | ------------------------- |
| v0.27.8           | v1.27.8                   |
| v0.26.8           | v1.26.7                   |

## Turning it on

  The `scheduler_plugins_enabled` option is used to enable the installation of scheduler plugins.

- For single-scheduler mode:

  Just pass `kube_scheduler_profiles` option to specify the scheduler profiles.

- For second-scheduler mode:

  You can enable or disable some plugins by setting the `scheduler_plugins_enabled_plugins` or `scheduler_plugins_disabled_plugins` option. They must be in the list we mentioned above.

  In addition, to use custom plugin configuration, set a value for `scheduler_plugins_plugin_config` option.

  For example, for Coscheduling plugin, you want to customize the permit waiting timeout to 10 seconds:

  ```yaml
  scheduler_plugins_plugin_config:
    - name: Coscheduling
      args:
        permitWaitingTimeSeconds: 10 # default is 60
  ```

  And more options can be found in the [main.yml](../../roles/kubernetes-apps/scheduler_plugins/defaults/main.yml).

## Leverage plugin

  Once the plugin is installed, we can apply CRs into cluster. For example, if using `CoScheduling`, we can apply the CR and test the deployment in the [example](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/doc/install.md#test-coscheduling).
