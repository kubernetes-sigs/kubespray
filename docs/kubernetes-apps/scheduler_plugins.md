# Scheduler plugins for Kubernetes

[`scheduler-plugins`](https://github.com/kubernetes-sigs/scheduler-plugins) is out-of-tree scheduler plugins based on the [scheduler framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/).

The kube-scheduler binary includes a list of plugins. But We only integrate some of them currently. The reasons for that are:

- Some plugins need to run a separate scheduler pod, meaning that there are at least two schedulers in the cluster. Running multi-scheduler will inevitably encounter resource conflicts when the cluster is short of resources. Therefore, it is not recommended in the production env.  
- Some plugins are still in Alpha stage(not stable enough).

So we will be using an unified scheduler and hence keep the resources conflict-free. That means we should replace the default-scheduler, there are some automatic jobs coming in Kubespray, we need to ensure that doesn't break anything.

## Compatibility Matrix

There are requirements for the version of Kubernetes, please see [Compatibility Matrix
](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master?tab=readme-ov-file#compatibility-matrix). It deserves our attention.

## Current integrated plugins

- [CoScheduling](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/coscheduling) [Beta]
- [CapacityScheduling](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/capacityscheduling) [Beta]
- [NodeResources](https://github.com/kubernetes-sigs/scheduler-plugins/tree/master/pkg/noderesources) [Beta]

## Turning it on

  The `scheduler_plugins_enabled` option is used to enable the scheduler plugins. It will install scheduler controller first, but then it won't install any plugins if the option `scheduler_plugins` is set empty, it's possible to install plugins manually after the completion of cluster provisioning.

  So, set a value to `scheduler_plugins` option, plugins will be installed when the cluster is provisioning by Kubespray. It must be in [support list](#current-integrated-plugins).

  In addition, to use custom scheduler configuration, set a value for `scheduler_plugins_custom_profile` option. Note that it only changes the profile of `default-scheduler`.

## Leverage plugin

  Once the plugin is installed, we can apply CRs into cluster. For example, if using `CoScheduling`, we can apply the CR and test the deployment in the [example](https://github.com/kubernetes-sigs/scheduler-plugins/blob/master/doc/install.md#test-coscheduling).
