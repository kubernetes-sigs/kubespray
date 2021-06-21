# gVisor

[gVisor](https://gvisor.dev/docs/) is an application kernel, written in Go, that implements a substantial portion of the Linux system call interface. It provides an additional layer of isolation between running applications and the host operating system.

gVisor includes an Open Container Initiative (OCI) runtime called runsc that makes it easy to work with existing container tooling. The runsc runtime integrates with Docker and Kubernetes, making it simple to run sandboxed containers.

## Usage

To enable gVisor you should be using a container manager that is compatible with selecting the [RuntimeClass](https://kubernetes.io/docs/concepts/containers/runtime-class/) such as `containerd`.

Containerd support:

```yaml
container_manager: containerd
gvisor_enabled: true
```
