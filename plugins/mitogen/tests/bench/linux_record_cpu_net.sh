#!/bin/bash

#
# Wrap a run of Ansible playbook so that CPU usage counters and network
# activity are logged to files.
#

[ ! "$1" ] && exit 1
sudo tcpdump -w $1-out.cap -s 0 host k1.botanicus.net &
date +%s.%N > $1-task-clock.csv
perf stat -x, -I 25 -e task-clock --append -o $1-task-clock.csv ansible-playbook run_hostname_100_times.yml
sudo pkill -f tcpdump
