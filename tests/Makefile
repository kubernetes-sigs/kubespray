create-tf:
	./scripts/create-tf.sh

delete-tf:
	./scripts/delete-tf.sh

$(ANSIBLE_INVENTORY):
	mkdir $@

create-packet: | $(ANSIBLE_INVENTORY)
	ansible-playbook cloud_playbooks/create-kubevirt.yml -c local \
		-e @"files/${CI_JOB_NAME}.yml"

delete-packet: ;

create-vagrant: | $(ANSIBLE_INVENTORY)
	vagrant up
	cp $(CI_PROJECT_DIR)/.vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory $|

delete-vagrant:
	vagrant destroy -f
