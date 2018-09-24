INVENTORY=$(PWD)/../inventory/sample/${CI_JOB_NAME}.ini
INVENTORY_YML=$(PWD)/../inventory/sample/${CI_JOB_NAME}.yml

$(HOME)/.ssh:
	mkdir -p $(HOME)/.ssh

init-gce: $(HOME)/.ssh
	# echo $(GCE_PEM_FILE) | base64 -d > $(HOME)/.ssh/gce
	echo $(PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/gce.private
	chmod 400 $(HOME)/.ssh/gce.private
	echo "$(GCE_CREDENTIALS_B64)" | base64 -d > $(HOME)/.ssh/gce.json

init-do: $(HOME)/.ssh
	echo $(DO_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/do.private
	chmod 400 $(HOME)/.ssh/do.private


init-packet: $(HOME)/.ssh
	echo $(PACKET_VM_PRIVATE_KEY) | base64 -d > $(HOME)/.ssh/packet.private
	chmod 400 $(HOME)/.ssh/packet.private

create-gce: init-gce
	ansible-playbook cloud_playbooks/create-gce.yml -i local_inventory/hosts.cfg -c local \
	$(LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e gce_credentials_file=$(HOME)/.ssh/gce.json \
	-e gce_project_id=$(GCE_PROJECT_ID) \
	-e gce_service_account_email=$(GCE_ACCOUNT) \
	-e inventory_path=$(INVENTORY) \
	-e test_id=$(TEST_ID) \
	-e preemptible=$(GCE_PREEMPTIBLE)

delete-gce:
	ansible-playbook -i $(INVENTORY) cloud_playbooks/delete-gce.yml -c local \
	$(LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e test_id=$(TEST_ID) \
	-e gce_project_id=$(GCE_PROJECT_ID) \
	-e gce_service_account_email=$(GCE_ACCOUNT) \
	-e gce_credentials_file=$(HOME)/.ssh/gce.json \
	-e inventory_path=$(INVENTORY)

create-do: init-do
	ansible-playbook cloud_playbooks/create-do.yml -i local_inventory/hosts.cfg -c local \
	${LOG_LEVEL} \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e inventory_path=$(INVENTORY) \
	-e test_id=${TEST_ID}

create-packet: init-packet
	ansible-playbook cloud_playbooks/create-packet.yml -i local_inventory/hosts.cfg \
	-e action=start -c local \
	-vvv \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e inventory_path=$(INVENTORY_YML) \
	-e test_id=${TEST_ID}


delete-packet: init-packet
	echo ' \
	ansible-playbook cloud_playbooks/create-packet.yml -i local_inventory/hosts.cfg -e action=destroy -c local \
	${LOG_LEVEL} \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e inventory_path=$(INVENTORY) \
	-e test_id=${TEST_ID}'


delete-do:
	ansible-playbook -i $(INVENTORY) cloud_playbooks/create-do.yml -c local \
	$(LOG_LEVEL) \
	-e @"files/${CI_JOB_NAME}.yml" \
	-e state=absent \
	-e test_id=${TEST_ID} \
	-e inventory_path=$(INVENTORY)
