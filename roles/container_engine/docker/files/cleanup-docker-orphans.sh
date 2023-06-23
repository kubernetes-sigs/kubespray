#!/bin/bash
list_descendants ()
{
  local children=$(ps -o pid= --ppid "$1")
  for pid in $children
  do
    list_descendants "$pid"
  done
  [[ -n "$children" ]] && echo "$children"
}

shim_search="^docker-containerd-shim|^containerd-shim"
count_shim_processes=$(pgrep -f $shim_search | wc -l)

if [ ${count_shim_processes} -gt 0 ]; then
        # Find all container pids from shims
        orphans=$(pgrep -P $(pgrep -d ',' -f $shim_search) |\
        # Filter out valid docker pids, leaving the orphans
        egrep -v $(docker ps -q | xargs docker inspect --format '{{.State.Pid}}' | awk '{printf "%s%s",sep,$1; sep="|"}'))

        if [[ -n "$orphans" && -n "$(ps -o ppid= $orphans)" ]]
        then
                # Get shim pids of orphans
                orphan_shim_pids=$(ps -o pid= $(ps -o ppid= $orphans))

                # Find all orphaned container PIDs
                orphan_container_pids=$(for pid in $orphan_shim_pids; do list_descendants $pid; done)

                # Recursively kill all child PIDs of orphan shims
                echo -e "Killing orphan container PIDs and descendants: \n$(ps -O ppid= $orphan_container_pids)"
                kill -9 $orphan_container_pids || true

        else
                echo "No orphaned containers found"
        fi
else
        echo "The node doesn't have any shim processes."
fi
