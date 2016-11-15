#!/bin/sh
# Generates MD formatted CI matrix from the .travis.yml
a=$(perl -ne '/^\s{6}(CLOUD_IMAGE|KUBE_NETWORK_PLUGIN|CLOUD_REGION|CLUSTER_MODE)=(\S+)$/ && print "$2\n"' .travis.yml)
printf "|%25s|%25s|%25s|%25s|\n" "Network plugin" "OS type" "GCE region" "Nodes layout"
echo "|-------------------------|-------------------------|-------------------------|-------------------------|"
c=0
for i in `echo $a`; do
  printf "|%25s" $i
  [ $(($c % 4)) -eq 3 ] && printf "|\n"
  c=$(( c + 1))
done
