init-packet:
	mkdir -p $(HOME)/.ssh
	echo $(PACKET_VM_SSH_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa
	chmod 400 $(HOME)/.ssh/id_rsa

create-tf:
	./scripts/create-tf.sh

delete-tf:
	./scripts/delete-tf.sh

$(INVENTORY_DIR):
	mkdir $@

create-packet: init-packet | $(INVENTORY_DIR)
	ansible-playbook cloud_playbooks/create-packet.yml -c local \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e test_name="$(subst .,-,$(CI_PIPELINE_ID)-$(CI_JOB_ID))" \
	-e branch="$(CI_COMMIT_BRANCH)" \
	-e pipeline_id="$(CI_PIPELINE_ID)" \
	-e inventory_path=$|

delete-packet: ;

create-vagrant: | $(INVENTORY_DIR)
	vagrant up
	cp $(CI_PROJECT_DIR)/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory $|

delete-vagrant:
	vagrant destroy -f
