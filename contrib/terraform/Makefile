providers := openstack aws exoscale hetzner vsphere opennebula upcloud

.PHONY: validate $(providers)

validate: $(providers)

$(providers):
	tofu -chdir=$@ init
	tofu -chdir=$@ validate
	tofu -chdir=$@ fmt -check -diff
