#!/usr/bin/env bash

DIRNAME=$( dirname "$0" )
BASENAME=$( basename "$0" )

NAMESPACE="{{ monitoring_namespace }}"

if [ -z "${NAMESPACE}" ]; then
    NAMESPACE=monitoring
fi

DEFAULT_WAITING_TIMEOUT=150
WAITING_TIMEOUT="{{ prometheus_waiting_timeout }}" 
if [ -z "${WAITING_TIMEOUT}" ]; then
    WAITING_TIMEOUT="${DEFAULT_WAITING_TIMEOUT}"
fi

if ! [ "${WAITING_TIMEOUT}" -eq "${WAITING_TIMEOUT}" ]; then
    WAITING_TIMEOUT="${DEFAULT_WAITING_TIMEOUT}"
fi

kctl() {
    kubectl --namespace "$NAMESPACE" "$@"
}

printf "Waiting while Operator registers custom resource definitions... "
for i in $(seq 1 "${WAITING_TIMEOUT}" )
do
  echo -n "."
  sleep 1
  kctl get customresourcedefinitions servicemonitors.monitoring.coreos.com > /dev/null 2>&1 || continue
  kctl get customresourcedefinitions prometheuses.monitoring.coreos.com    > /dev/null 2>&1 || continue
  kctl get customresourcedefinitions alertmanagers.monitoring.coreos.com   > /dev/null 2>&1 || continue
  kctl get servicemonitors.monitoring.coreos.com                           > /dev/null 2>&1 || continue
  kctl get prometheuses.monitoring.coreos.com                              > /dev/null 2>&1 || continue
  kctl get alertmanagers.monitoring.coreos.com                             > /dev/null 2>&1 || continue
  echo " done!"
  exit 0
done

echo
echo "ERROR: Timeout is reached: ${WAITING_TIMEOUT}"
echo "ERROR: Prometheus Operator is not ready"
exit 1



