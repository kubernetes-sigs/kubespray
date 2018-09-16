#!/bin/bash

## Get the children and grand children of a parent process ##
list_descendants ()
{
  local children=$(ps -o pid= --ppid "$1")
  for pid in $children
  do
    list_descendants "$pid"
  done
  [[ -n "$children" ]] && echo "$children"
}

current_time=$(date +'%Y%m%d-%H%M%S')
is_docker_active=$([ `systemctl is-active docker` = "active" ] && echo true || echo false)


if [ ${is_docker_active} == "true" ]; then
   # Get the storage driver
   docker_storage_driver=$(docker info -f '{{.Driver}}')
   # Attempt to kill containers gracefully before stopping dockeryup it does
   timeout 180 docker kill -s TERM $(docker ps -q)
   timeout 180 systemctl stop docker
fi

count_shim_processes=$(pgrep -f ^docker-containerd-shim | wc -l)

if [ ${count_shim_processes} -gt 0 ]; then
  #Recursively kill child processes of containers
  kill -9 $(for pid in $(pgrep -f ^docker-containerd-shim); do list_descendants $pid; done) || true

  # Kill container parent processes
  pkill -KILL -f ^docker-containerd-shim || true
fi

# Cleanup kubelet directory
for kubeletattempt in {1..3}
do
  for i in $(mount|grep kubelet|awk '{print $3}'); do timeout 120 umount $i || true; done
done

if [ -d "/var/lib/kubelet/pods/" ]; then
  mv /var/lib/kubelet/pods/ /var/lib/kubelet/deadpods-${current_time}/
  nohup rm -rf /var/lib/kubelet/deadpods-${current_time}/ >/dev/null 2>&1 &
fi
if [ -d "/var/lib/kubelet/plugins" ]; then
  mv /var/lib/kubelet/plugins /var/lib/kubelet/deadplugins-${current_time}
  nohup rm -rf /var/lib/kubelet/deadplugins-${current_time}/ >/dev/null 2>&1 &
fi

# Cleanup docker directory
for dockerattempt in {1..3}
do
  for i in $(mount|grep ${DOCKER_DAEMON_GRAPH}|awk '{print $3}'); do timeout 120 umount $i || true; done
done

if [ -d "${DOCKER_DAEMON_GRAPH}" ]; then
  if [ -n "${docker_storage_driver}" ]; then
  	timeout 120 umount ${DOCKER_DAEMON_GRAPH}/${docker_storage_driver} || true
  else
  	for storage_driver in devicemapper overlay2 overlay zfs vfs aufs btrfs
  	do
  		[ -d "${DOCKER_DAEMON_GRAPH}/${storage_driver}" ] && ( timeout 120 umount ${DOCKER_DAEMON_GRAPH}/${storage_driver} || true )
  	done
  fi
  mv ${DOCKER_DAEMON_GRAPH} $(dirname "${DOCKER_DAEMON_GRAPH}")/deaddocker-${current_time}/
  nohup rm -rf $(dirname "${DOCKER_DAEMON_GRAPH}")/deaddocker-${current_time}/ >/dev/null 2>&1 &
fi
