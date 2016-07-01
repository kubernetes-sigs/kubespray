#!/bin/bash

if [ -n "$1" ] ; then
  NS="--namespace=$1"
fi

kubectl get nodes || exit 1

echo "Installing netchecker server"
git clone https://github.com/adidenko/netchecker-server
pushd netchecker-server
  pushd docker
    docker build -t 127.0.0.1:31500/netchecker/server:latest .
    docker push 127.0.0.1:31500/netchecker/server:latest
  popd
  kubectl create -f netchecker-server_pod.yaml $NS
  kubectl create -f netchecker-server_svc.yaml $NS
popd

echo "Installing netchecker agents"
git clone https://github.com/adidenko/netchecker-agent
pushd netchecker-agent
  pushd docker
    docker build -t 127.0.0.1:31500/netchecker/agent:latest .
    docker push 127.0.0.1:31500/netchecker/agent:latest
  popd
  kubectl get nodes | grep Ready | awk '{print $1}' | xargs -I {} kubectl label nodes {} netchecker=agent
  NUMNODES=`kubectl get nodes --show-labels | grep Ready | grep netchecker=agent | wc -l`
  sed -e "s/replicas:.*/replicas: $NUMNODES/g" -i netchecker-agent_rc.yaml
  kubectl create -f netchecker-agent_rc.yaml $NS
popd

echo "DONE"
curl -s -X GET 'http://localhost:31081/api/v1/agents/' | python -mjson.tool
echo
echo "use the following command to check agents:"
echo "curl -s -X GET 'http://localhost:31081/api/v1/agents/' | python -mjson.tool"
