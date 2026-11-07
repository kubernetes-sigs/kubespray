all: start install
.PHONY : all

start:
	ansible-playbook --connection=local --inventory=localhost -e @local/vars.yml start.yml

install:
	(cd ../../ && ansible-playbook -i contrib/lima/local/hosts.yml -e @contrib/lima/local/kubespray.yml -b cluster.yml)

stop:
	ansible-playbook --connection=local --inventory=localhost -e @local/vars.yml stop.yml
	rm local/hosts.yml
