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
	-e @"files/${CI_JOB_NAME}.yml" \
	-e test_name="$(subst .,-,$(CI_PIPELINE_ID)-$(CI_JOB_ID))" \
	-e branch="$(CI_COMMIT_BRANCH)" \
	-e pipeline_id="$(CI_PIPELINE_ID)" \
	-e inventory_path=$(INVENTORY_DIR)

delete-packet: ;

create-vagrant:
	vagrant up
	cp $(CI_PROJECT_DIR)/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory $(INVENTORY_DIR)

delete-vagrant:
	vagrant destroy -f
