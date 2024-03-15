INVENTORY=$(PWD)/../inventory/sample/${CI_JOB_NAME}-${BUILD_NUMBER}.ini

init-packet:
	mkdir -p $(HOME)/.ssh
	echo $(PACKET_VM_SSH_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa
	chmod 400 $(HOME)/.ssh/id_rsa

create-tf:
	./scripts/create-tf.sh

delete-tf:
	./scripts/delete-tf.sh

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
