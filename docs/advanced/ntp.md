# NTP synchronization

The Network Time Protocol (NTP) is a networking protocol for clock synchronization between computer systems. Time synchronization is important to Kubernetes and Etcd.

## Enable the NTP

To start the ntpd(or chrony) service and enable it at system boot. There are related specific variables:

```ShellSession
ntp_enabled: true
```

The NTP service would be enabled and sync time automatically.

## Customize the NTP configure file

In the Air-Gap environment, the node cannot access the NTP server by internet. So the node can use the customized ntp server by configuring ntp file.

```ShellSession
ntp_enabled: true
ntp_manage_config: true
ntp_servers:
  - "0.your-ntp-server.org iburst"
  - "1.your-ntp-server.org iburst"
  - "2.your-ntp-server.org iburst"
  - "3.your-ntp-server.org iburst"
```

## Setting the TimeZone

The timezone can also be set by the `ntp_timezone` , eg: "Etc/UTC","Asia/Shanghai". If not set, the timezone will not change.

```ShellSession
ntp_enabled: true
ntp_timezone: Etc/UTC
```

## Advanced Configure

Enable `tinker panic` is useful when running NTP in a VM environment to avoiding clock drift on VMs. It only takes effect when ntp_manage_config is true.

```ShellSession
ntp_tinker_panic: true
```

Force sync time immediately by NTP after the ntp installed, which is useful in newly installed system.

```ShellSession
ntp_force_sync_immediately: true
```
