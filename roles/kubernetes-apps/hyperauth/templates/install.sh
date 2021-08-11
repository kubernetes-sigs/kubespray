#!/bin/bash

source hyperauth.config
set -x

# step 0  - sed manifests
if [ $REGISTRY != "{REGISTRY}" ]; then
  sed -i 's#postgres#'${REGISTRY}'/postgres#g' 1.initialization.yaml
  sed -i 's#tmaxcloudck/hyperauth#'${REGISTRY}'/hyperauth#g' 2.hyperauth_deployment.yaml
  sed -i 's#wurstmeister/zookeeper#'${REGISTRY}'/zookeeper#g' 4.kafka_all.yaml
  sed -i 's#wurstmeister/kafka#'${REGISTRY}'/kafka#g' 4.kafka_all.yaml
  sed -i 's#tmaxcloudck/hyperauth-log-collector#'${REGISTRY}'/hyperauth_log_collector#g' 5.hyperauth-log-collector.yaml
fi

sed -i 's/{POSTGRES_VERSION}/'${POSTGRES_VERSION}'/g' 1.initialization.yaml
sed -i 's/{HYPERAUTH_VERSION}/'${HYPERAUTH_VERSION}'/g' 2.hyperauth_deployment.yaml
sed -i 's/{ZOOKEEPER_VERSION}/'${ZOOKEEPER_VERSION}'/g' 4.kafka_all.yaml
sed -i 's/{KAFKA_VERSION}/'${KAFKA_VERSION}'/g' 4.kafka_all.yaml
sed -i 's/{KAFKA1_EXTERNAL_IP}/'${KAFKA1_EXTERNAL_IP}'/g' 4.kafka_all.yaml
sed -i 's/{KAFKA2_EXTERNAL_IP}/'${KAFKA2_EXTERNAL_IP}'/g' 4.kafka_all.yaml
sed -i 's/{KAFKA3_EXTERNAL_IP}/'${KAFKA3_EXTERNAL_IP}'/g' 4.kafka_all.yaml

sed -i 's/{HYPERAUTH_LOG_COLLECTOR_VERSION}/'${HYPERAUTH_LOG_COLLECTOR_VERSION}'/g' 5.hyperauth_log_collector.yaml


# step1 1.initialization.yaml
kubectl apply -f 1.initialization.yaml

sleep 60

# step2 Generate Certs for hyperauth & kafka
chmod +755 generateCerts.sh
./generateCerts.sh -ip=$(kubectl describe service hyperauth -n hyperauth | grep 'LoadBalancer Ingress' | cut -d ' ' -f7)
kubectl create secret tls hyperauth-https-secret --cert=./hyperauth.crt --key=./hyperauth.key -n hyperauth
cp hypercloud-root-ca.crt /etc/kubernetes/pki/hypercloud-root-ca.crt
cp hypercloud-root-ca.key /etc/kubernetes/pki/hypercloud-root-ca.key
  
keytool -keystore hyperauth.truststore.jks -alias ca-cert -import -file /etc/kubernetes/pki/hypercloud-root-ca.crt -storepass tmax@23 -noprompt
keytool -keystore hyperauth.keystore.jks -alias hyperauth -validity 3650 -genkey -keyalg RSA -dname "CN=hyperauth" -storepass tmax@23 -keypass tmax@23
keytool -keystore hyperauth.keystore.jks -alias hyperauth -certreq -file ca-request-hyperauth -storepass tmax@23
openssl x509 -req -CA /etc/kubernetes/pki/hypercloud-root-ca.crt -CAkey /etc/kubernetes/pki/hypercloud-root-ca.key -in ca-request-hyperauth -out ca-signed-hyperauth -days 3650 -CAcreateserial
keytool -keystore hyperauth.keystore.jks -alias ca-cert -import -file /etc/kubernetes/pki/hypercloud-root-ca.crt -storepass tmax@23 -noprompt
keytool -keystore hyperauth.keystore.jks -alias hyperauth -import -file ca-signed-hyperauth -storepass tmax@23 -noprompt
kubectl create secret generic hyperauth-kafka-jks --from-file=./hyperauth.keystore.jks --from-file=./hyperauth.truststore.jks -n hyperauth
rm ca-*
 
##For Kafka-Brokers
keytool -keystore kafka.broker.truststore.jks -alias ca-cert -import -file /etc/kubernetes/pki/hypercloud-root-ca.crt -storepass tmax@23 -noprompt
keytool -keystore kafka.broker.keystore.jks -alias broker -validity 3650 -genkey -keyalg RSA -dname "CN=kafka" -storepass tmax@23 -keypass tmax@23
keytool -keystore kafka.broker.keystore.jks -alias broker -certreq -file ca-request-broker -storepass tmax@23
cat > "kafka.cnf" <<EOL
[kafka]
subjectAltName = DNS:kafka-1.hyperauth,DNS:kafka-2.hyperauth,DNS:kafka-3.hyperauth${KAFKA_EXTERNAL_URL}
EOL
sudo openssl x509 -req -CA /etc/kubernetes/pki/hypercloud-root-ca.crt -CAkey /etc/kubernetes/pki/hypercloud-root-ca.key -in ca-request-broker -out ca-signed-broker -days 3650 -CAcreateserial -extfile "kafka.cnf" -extensions kafka -sha256
keytool -keystore kafka.broker.keystore.jks -alias ca-cert -import -file /etc/kubernetes/pki/hypercloud-root-ca.crt -storepass tmax@23 -noprompt
keytool -keystore kafka.broker.keystore.jks -alias broker -import -file ca-signed-broker -storepass tmax@23 -noprompt
kubectl create secret generic kafka-jks --from-file=./kafka.broker.keystore.jks --from-file=./kafka.broker.truststore.jks -n hyperauth

## 다중화
IFS=' ' read -r -a masters <<< $(kubectl get nodes --selector=node-role.kubernetes.io/master -o jsonpath='{$.items[*].status.addresses[?(@.type=="InternalIP")].address}')
for master in "${masters[@]}"
do
	if [ $master == $MAIN_MASTER_IP ]; then
    continue
	fi
	sshpass -p "$MASTER_NODE_ROOT_PASSWORD" scp hypercloud-root-ca.crt ${MASTER_NODE_ROOT_USER}@"$master":/etc/kubernetes/pki/hypercloud-root-ca.crt
done	

# step3 Hyperauth Deploymennt

## DB IP Sed 해야 할지 아직 판단이 안섬
kubectl apply -f 2.hyperauth_deployment.yaml

# step4 Kafka Deployment
kubectl apply -f 4.kafka_init.yaml
kubectl apply -f 5.kafka_deployment.yaml

# step5 oidc with kubernetes ( modify kubernetes api-server manifest )
cp /etc/kubernetes/manifests/kube-apiserver.yaml .
export ip=`kubectl describe service hyperauth -n hyperauth | grep 'LoadBalancer Ingress' | cut -d ' ' -f7`
yq e '.spec.containers[0].command += "--oidc-issuer-url=https://'$ip'/auth/realms/tmax"' -i ./kube-apiserver.yaml
yq e '.spec.containers[0].command += "--oidc-client-id=hypercloud5"' -i ./kube-apiserver.yaml
yq e '.spec.containers[0].command += "--oidc-username-claim=preferred_username"' -i ./kube-apiserver.yaml
yq e '.spec.containers[0].command += "--oidc-username-prefix=-"' -i ./kube-apiserver.yaml
yq e '.spec.containers[0].command += "--oidc-groups-claim=group"' -i ./kube-apiserver.yaml
mv -f ./kube-apiserver.yaml /etc/kubernetes/manifests/kube-apiserver.yaml
