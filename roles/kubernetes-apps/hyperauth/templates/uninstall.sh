#!/bin/bash

source hyperauth.config
set -x

# step 1 - delete Hyperauth component
timeout 5m kubectl delete -f 5.kafka_deployment.yaml
suc=`echo $?`
if [ $suc != 0 ]; then
  echo "Failed to delete 5.kafka_deployment.yaml"
fi
timeout 5m kubectl delete -f 4.kafka_init.yaml
suc=`echo $?`
if [ $suc != 0 ]; then
  echo "Failed to delete 4.kafka_init.yaml"
fi
timeout 5m kubectl delete -f 2.hyperauth_deployment.yaml
suc=`echo $?`
if [ $suc != 0 ]; then
  echo "Failed to delete 2.hyperauth_deployment.yaml"
fi


# step 4 - delete hyperauth namespace
timeout 5m kubectl delete -f 1.initialization.yaml
suc=`echo $?`
if [ $suc != 0 ]; then
  echo "Failed to delete 1.initialization.yaml"
fi

# step 5 - delete Kubernetes oidc settings
cp /etc/kubernetes/manifests/kube-apiserver.yaml .
yq eval 'del(.spec.containers[0].command[] | select(. == "--oidc-*") )' -i kube-apiserver.yaml
mv -f ./kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml

rm /etc/kubernetes/pki/hypercloud-root-ca.*

IFS=' ' read -r -a masters <<< $(kubectl get nodes --selector=node-role.kubernetes.io/master -o jsonpath='{$.items[*].status.addresses[?(@.type=="InternalIP")].address}')
for master in "${masters[@]}"
do
  if [ $master == $MAIN_MASTER_IP ]; then
    continue
  fi

  sshpass -p "$MASTER_NODE_ROOT_PASSWORD" ssh -o StrictHostKeyChecking=no ${MASTER_NODE_ROOT_USER}@"$master" sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml .
  sshpass -p "$MASTER_NODE_ROOT_PASSWORD" ssh -o StrictHostKeyChecking=no ${MASTER_NODE_ROOT_USER}@"$master" 'sudo yq eval '"'"'del(.spec.containers[0].command[] | select(. == "--oidc-*") )'"'"' -i kube-apiserver.yaml'
  sshpass -p "$MASTER_NODE_ROOT_PASSWORD" ssh -o StrictHostKeyChecking=no ${MASTER_NODE_ROOT_USER}@"$master" sudo mv -f ./kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml

  sshpass -p "$MASTER_NODE_ROOT_PASSWORD" ssh -o StrictHostKeyChecking=no ${MASTER_NODE_ROOT_USER}@"$master" sudo rm /etc/kubernetes/pki/hypercloud-root-ca.*
done
