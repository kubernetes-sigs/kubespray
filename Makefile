mitogen:
	ansible-playbook -c local mitogen.yaml -vv
clean:
	rm -rf dist/
	rm *.retry
