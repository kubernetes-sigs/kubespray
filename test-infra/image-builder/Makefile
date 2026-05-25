docker_host ?= quay.io
docker_login ?= true
docker_user ?= kubespray+buildvmimages
registry ?= quay.io/kubespray
staging_registry ?= us-central1-docker.pkg.dev/k8s-staging-images/kubespray

deploy:
	ansible-playbook -i hosts.ini \
		-e docker_host=$(docker_host) \
		-e docker_login=$(docker_login) \
		-e docker_user=$(docker_user) \
		-e docker_password=$(docker_password) \
		-e registry=$(registry) \
		cluster.yml

push-docker:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e docker_host=$(docker_host) \
		-e docker_login=$(docker_login) \
		-e docker_user=$(docker_user) \
		-e docker_password=$(docker_password) \
		-e registry=$(registry) \
		-e '{"kubevirt_images_push": true, "kubevirt_container_builder": "docker", "kubevirt_images_target_host": "localhost"}' \
		cluster.yml

push-single-docker:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e docker_host=$(docker_host) \
		-e docker_login=$(docker_login) \
		-e docker_user=$(docker_user) \
		-e docker_password=$(docker_password) \
		-e registry=$(registry) \
		-e '{"kubevirt_images_push": true, "kubevirt_container_builder": "docker", "kubevirt_images_target_host": "localhost", "kubevirt_images_selected": ["$(image_name)"]}' \
		cluster.yml

push-single-staging:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e docker_host=us-central1-docker.pkg.dev \
		-e registry=$(staging_registry) \
		-e '{"docker_login": false, "kubevirt_images_push": true, "kubevirt_container_builder": "docker", "kubevirt_images_target_host": "localhost", "kubevirt_images_selected": ["$(image_name)"]}' \
		cluster.yml

validate:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e kubevirt_buildkit_output_dir=$(CURDIR)/.image-builder/buildkit-output \
		-e '{"kubevirt_images_push": false, "kubevirt_container_builder": "buildkit", "kubevirt_images_target_host": "localhost"}' \
		cluster.yml

validate-single:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e kubevirt_buildkit_output_dir=$(CURDIR)/.image-builder/buildkit-output \
		-e '{"kubevirt_images_push": false, "kubevirt_container_builder": "buildkit", "kubevirt_images_target_host": "localhost", "kubevirt_images_selected": ["$(image_name)"]}' \
		cluster.yml

validate-docker:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e '{"kubevirt_images_push": false, "kubevirt_container_builder": "docker", "kubevirt_images_target_host": "localhost"}' \
		cluster.yml

validate-single-docker:
	ansible-playbook -i localhost, -c local \
		-e images_dir=$(CURDIR)/.image-builder \
		-e '{"kubevirt_images_push": false, "kubevirt_container_builder": "docker", "kubevirt_images_target_host": "localhost", "kubevirt_images_selected": ["$(image_name)"]}' \
		cluster.yml
