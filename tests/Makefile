INVENTORY=$(PWD)/../inventory/sample/${CI_JOB_NAME}-${BUILD_NUMBER}.ini

$(HOME)/.ssh/id_rsa:
	mkdir -p $(HOME)/.ssh
	echo $(PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa
	chmod 400 $(HOME)/.ssh/id_rsa

init-gce: $(HOME)/.ssh/id_rsa
	# echo $(GCE_PEM_FILE) | base64 -d > $(HOME)/.ssh/gce
	echo "$(GCE_CREDENTIALS_B64)" | base64 -d > $(HOME)/.ssh/gce.json

init-do: $(HOME)/.ssh/id_rsa
	echo $(DO_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa

init-packet:
	echo $(PACKET_VM_SSH_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa
	chmod 400 $(HOME)/.ssh/id_rsa

create-tf:
	./scripts/create-tf.sh

delete-tf:
	./scripts/delete-tf.sh

create-gce: init-gce
	ansible-playbook cloud_playbooks/create-gce.yml -i local_inventory/hosts.cfg -c local \
	$(ANSIBLE_LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e gce_credentials_file=$(HOME)/.ssh/gce.json \
	-e gce_project_id=$(GCE_PROJECT_ID) \
	-e gce_service_account_email=$(GCE_ACCOUNT) \
	-e inventory_path=$(INVENTORY) \
	-e test_id=$(TEST_ID) \
	-e preemptible=$(GCE_PREEMPTIBLE)


delete-gce:
	ansible-playbook -i $(INVENTORY) cloud_playbooks/delete-gce.yml -c local \
	$(ANSIBLE_LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e test_id=$(TEST_ID) \
	-e gce_project_id=$(GCE_PROJECT_ID) \
	-e gce_service_account_email=$(GCE_ACCOUNT) \
	-e gce_credentials_file=$(HOME)/.ssh/gce.json \
	-e inventory_path=$(INVENTORY)

create-do: init-do
	ansible-playbook cloud_playbooks/create-do.yml -i local_inventory/hosts.cfg -c local \
	${ANSIBLE_LOG_LEVEL} \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e inventory_path=$(INVENTORY) \
	-e test_id=${TEST_ID}

delete-do:
	ansible-playbook -i $(INVENTORY) cloud_playbooks/create-do.yml -c local \
	$(ANSIBLE_LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e state=absent \
	-e test_id=${TEST_ID} \
	-e inventory_path=$(INVENTORY)

create-packet: init-packet
	ansible-playbook cloud_playbooks/create-packet.yml -c local \
	$(ANSIBLE_LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e test_id=$(TEST_ID) \
	-e branch="$(CI_COMMIT_BRANCH)" \
	-e pipeline_id="$(CI_PIPELINE_ID)" \
	-e inventory_path=$(INVENTORY)

delete-packet:
	ansible-playbook cloud_playbooks/delete-packet.yml -c local \
	$(ANSIBLE_LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e test_id=$(TEST_ID) \
	-e branch="$(CI_COMMIT_BRANCH)" \
	-e pipeline_id="$(CI_PIPELINE_ID)" \
	-e inventory_path=$(INVENTORY)

cleanup-packet:
	ansible-playbook cloud_playbooks/cleanup-packet.yml -c local \
	$(ANSIBLE_LOG_LEVEL)

create-vagrant:
	vagrant up
	find / -name vagrant_ansible_inventory
	cp  /builds/kargo-ci/kubernetes-sigs-kubespray/inventory/sample/vagrant_ansible_inventory $(INVENTORY)

delete-vagrant:
	vagrant destroy -f
