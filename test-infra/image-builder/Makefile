deploy:
	ansible-playbook -i hosts.ini -e docker_password=$(docker_password) cluster.yml

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
