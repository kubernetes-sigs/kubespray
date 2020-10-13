docker build -t kubespray:${1} . --no-cache
docker tag kubespray:${1} certified-registry.rcplatform.io/kubespray/kubespray:${1}
docker push certified-registry.rcplatform.io/kubespray/kubespray:${1}