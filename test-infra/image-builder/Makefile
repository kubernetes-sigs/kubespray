deploy:
	ansible-playbook -i hosts.ini -e docker_password=$(docker_password) cluster.yml

validate:
	ansible-playbook -i hosts.ini -e '{"kubevirt_images_push": false}' cluster.yml

validate-single:
	ansible-playbook -i hosts.ini -e '{"kubevirt_images_push": false, "kubevirt_images_selected": ["$(image_name)"]}' cluster.yml
