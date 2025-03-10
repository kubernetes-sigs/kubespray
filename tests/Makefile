init-packet:
	mkdir -p $(HOME)/.ssh
	echo $(PACKET_VM_SSH_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/id_rsa
	chmod 400 $(HOME)/.ssh/id_rsa

create-tf:
	./scripts/create-tf.sh

delete-tf:
	./scripts/delete-tf.sh

$(ANSIBLE_INVENTORY):
	mkdir $@

create-packet: init-packet | $(ANSIBLE_INVENTORY)
	ansible-playbook cloud_playbooks/create-packet.yml -c local \
		-e @"files/${CI_JOB_NAME}.yml"

delete-packet: ;

create-vagrant: | $(ANSIBLE_INVENTORY)
	vagrant up
	cp $(CI_PROJECT_DIR)/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory $|

delete-vagrant:
	vagrant destroy -f
