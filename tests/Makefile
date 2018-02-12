$(HOME)/.ssh/id_rsa:
	mkdir -p $(HOME)/.ssh
	echo $(PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa
	chmod 400 $(HOME)/.ssh/id_rsa

init-gce: $(HOME)/.ssh/id_rsa
	# echo $(GCE_PEM_FILE) | base64 -d > $(HOME)/.ssh/gce
	echo "$(GCE_CREDENTIALS)" > $(HOME)/.ssh/gce.json


init-do: $(HOME)/.ssh/id_rsa
	pip install dopy
	echo $(DO_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa

create-gce: init-gce
	ansible-playbook cloud_playbooks/create-gce.yml -i local_inventory/hosts.cfg -c local \
	$(LOG_LEVEL) \
	-e @$(CI_TEST_VARS) \
	-e gce_credentials_file=$(HOME)/.ssh/gce.json \
	-e gce_project_id=$(GCE_PROJECT_ID) \
	-e gce_service_account_email=$(GCE_ACCOUNT) \
	-e inventory_path=$(PWD)/../inventory/sample/hosts.ini \
	-e test_id=$(TEST_ID) \
	-e preemptible=$(GCE_PREEMPTIBLE)


delete-gce:
	ansible-playbook -i ../inventory/sample/hosts.ini cloud_playbooks/delete-gce.yml -c local \
	$(LOG_LEVEL) \
	-e @$(CI_TEST_VARS) \
	-e test_id=$(TEST_ID) \
	-e gce_project_id=$(GCE_PROJECT_ID) \
	-e gce_service_account_email=$(GCE_ACCOUNT) \
	-e gce_credentials_file=$(HOME)/.ssh/gce.json \
	-e inventory_path=$(PWD)/inventory/sample/hosts.ini

create-do: init-do
	ansible-playbook cloud_playbooks/create-do.yml -i tests/local_inventory/hosts.cfg -c local \
	${LOG_LEVEL} \
	-e @$(CI_TEST_VARS) \
	-e inventory_path=${PWD}/../inventory/hosts.ini \
	-e test_id=${TEST_ID}


delete-do:
	ansible-playbook -i ../inventory/sample/hosts.ini tests/cloud_playbooks/create-do.yml -c local \
	$LOG_LEVEL \
	-e state=absent \
	-e test_id=${TEST_ID} \
	-e inventory_path=${PWD}/../inventory/inventory.ini \
