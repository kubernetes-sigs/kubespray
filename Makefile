mitogen:
	@echo Mitogen support is deprecated.
	@echo Please run the following command manually:
	@echo   ansible-playbook -c local mitogen.yml -vv

clean:
	rm -rf dist/
	rm *.retry

nodes:
	@echo tmux-cssh -o '-l ansible' rock-a01.k8s.loc rock-a02.k8s.loc rock-a03.k8s.loc
	@tmux-cssh -o '-l ansible' rock-a01.k8s.loc rock-a02.k8s.loc rock-a03.k8s.loc

install:
	@echo ansible-playbook -i inventory/cluster/hosts.yaml --user ansible --become --become-user=root cluster.yml
	@ansible-playbook -i inventory/cluster/hosts.yaml  --user ansible --become --become-user=root cluster.yml

info:
	@ansible-playbook -i inventory/cluster/hosts.yaml  --user ansible --become --become-user=root scripts/collect-info.yaml

etcd-check:
	@echo checking etcd service
	@echo make nodes
	@echo set -a
	@echo source /etc/etcd.env
	@echo set +a
	@echo /usr/local/bin/etcdctl endpoint --cluster health
	@echo /usr/local/bin/etcdctl endpoint --cluster status
	@echo /usr/local/bin/etcdctl endpoint --cluster hashkv
