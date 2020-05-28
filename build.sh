docker build -t  kubespray:${1} . --no-cache
docker tag kubespray:${1} staging.repo.rcplatform.io/kubespray/kubespray:${1}
docker push staging.repo.rcplatform.io/kubespray/kubespray:${1}