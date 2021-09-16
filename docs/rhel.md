# Red Hat Enterprise Linux (RHEL)

## RHEL Support Subscription Registration

In order to install packages via yum or dnf, RHEL 7/8 hosts are required to be registered for a valid Red Hat support subscription.

You can apply for a 1-year Development support subscription by creating a [Red Hat Developers](https://developers.redhat.com/) account. Be aware though that as the Red Hat Developers subscription is limited to only 1 year, it should not be used to register RHEL 7/8 hosts provisioned in Production environments.

Once you have a Red Hat support account, simply add the credentials to the Ansible inventory parameters `rh_subscription_username` and `rh_subscription_password` prior to deploying Kubespray. If your company has a Corporate Red Hat support account, then obtain an **Organization ID** and **Activation Key**, and add these to the Ansible inventory parameters `rh_subscription_org_id` and `rh_subscription_activation_key` instead of using your Red Hat support account credentials.

```ini
rh_subscription_username: ""
rh_subscription_password: ""
# rh_subscription_org_id: ""
# rh_subscription_activation_key: ""
```

Either the Red Hat support account username/password, or Organization ID/Activation Key combination must be specified in the Ansible inventory in order for the Red Hat subscription registration to complete successfully during the deployment of Kubespray.

Update the Ansible inventory parameters `rh_subscription_usage`, `rh_subscription_role` and `rh_subscription_sla` if necessary to suit your specific requirements.

```ini
rh_subscription_usage: "Development"
rh_subscription_role: "Red Hat Enterprise Server"
rh_subscription_sla: "Self-Support"
```

If the RHEL 7/8 hosts are already registered to a valid Red Hat support subscription via an alternative configuration management approach prior to the deployment of Kubespray, the successful RHEL `subscription-manager` status check will simply result in the RHEL subscription registration tasks being skipped.

## RHEL 8

RHEL 8 ships only with iptables-nft (ie without iptables-legacy)
The only tested configuration for now is using Calico CNI
You need to use K8S 1.17+ and to add `calico_iptables_backend: "NFT"` to your configuration

If you have containers that are using iptables in the host network namespace (`hostNetwork=true`),
you need to ensure they are using iptables-nft.
An example how k8s do the autodetection can be found [in this PR](https://github.com/kubernetes/kubernetes/pull/82966)
