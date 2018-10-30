mitogen:
	ansible-playbook -c local mitogen.yaml -vv
clean:
	rm -rf dist/
	rm *.retry

create-cluster:
	ansible-playbook -i inventory.ini etcd.yaml -vv  -b --become-user=root   -e etcd_action=create

upgrade-cluster:
	ansible-playbook -i inventory.ini etcd.yaml -vv  -b --become-user=root   -e etcd_action=upgrade

delete-cluster:
	ansible-playbook -i inventory.ini etcd.yaml -vv  -b --become-user=root   -e etcd_delete_cluster=true
